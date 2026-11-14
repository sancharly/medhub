import { lazy } from "react";
import type { ComponentType } from "react";

/** A route chunk could not be imported (network failure, or a deployment replaced the file). */
export class ChunkLoadError extends Error {
  readonly cause: unknown;

  constructor(cause: unknown) {
    super("A route chunk failed to load");
    this.name = "ChunkLoadError";
    this.cause = cause;
  }
}

// Lazy routes whose import failed and have not been rebuilt yet.
const failed = new Set<() => void>();

/**
 * Rebuild every lazy route whose import failed, so the next render imports it again. React caches a
 * rejected import for the life of the lazy component, so without this a retry would replay the
 * failure.
 */
export function reloadFailedChunks() {
  failed.forEach((rebuild) => rebuild());
  failed.clear();
}

/**
 * `React.lazy` for a routed page. A failed import surfaces as a `ChunkLoadError`, which
 * `RouteChunkBoundary` shows with a retry that calls `reloadFailedChunks` (SR-027 AC 3).
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function lazyRoute<C extends ComponentType<any>>(factory: () => Promise<{ default: C }>): C {
  const rebuild = () => {
    Inner = lazy(load);
  };
  const load = () =>
    factory().catch((error: unknown) => {
      failed.add(rebuild);
      throw new ChunkLoadError(error);
    });
  let Inner = lazy(load);

  // The wrapper keeps one stable component type for the router while `Inner` is replaced.
  const LazyRoute = (props: React.ComponentProps<C>) => <Inner {...props} />;
  return LazyRoute as unknown as C;
}
