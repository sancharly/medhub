import { Component } from "react";
import type { ReactNode } from "react";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChunkLoadError, reloadFailedChunks } from "./lazyRoute";

interface Props {
  /** A new value (the current path) clears a failure, so leaving the broken route recovers. */
  resetKey: string;
  children: ReactNode;
}

interface State {
  error: Error | null;
  /** The path that was current when the failure was caught; leaving it clears the failure. */
  errorKey: string | null;
  /** A retry has already been made on this path. */
  retried: boolean;
}

/**
 * Catches a route chunk that failed to load and offers a retry (SR-027 AC 3). Any other error is
 * rethrown to the next boundary (`AppErrorBoundary`), so a page's own bug is not reported as a
 * loading problem.
 */
export class RouteChunkBoundary extends Component<Props, State> {
  state: State = { error: null, errorKey: null, retried: false };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  // Runs on the render that follows the error, with the props of the failing render, so a failure
  // met while navigating is recorded against the new path and does not reset itself.
  static getDerivedStateFromProps(props: Props, state: State): Partial<State> | null {
    return state.error && state.errorKey === null ? { errorKey: props.resetKey } : null;
  }

  componentDidUpdate(prev: Props) {
    if (prev.resetKey !== this.props.resetKey) {
      if (this.state.error && this.state.errorKey !== this.props.resetKey) {
        reloadFailedChunks();
        this.setState({ error: null, errorKey: null, retried: false });
      } else if (this.state.retried && !this.state.error) {
        this.setState({ retried: false });
      }
    }
  }

  private retry() {
    reloadFailedChunks();
    this.setState({ error: null, errorKey: null, retried: true });
  }

  render() {
    const { error } = this.state;
    if (error) {
      if (!(error instanceof ChunkLoadError)) throw error;
      return (
        <Box role="alert" sx={{ p: 3, textAlign: "center" }} data-testid="route-chunk-error">
          <Typography variant="h6" gutterBottom>
            This page could not be loaded.
          </Typography>
          {this.state.retried ? (
            <>
              <Typography gutterBottom>
                The application may have been updated. Reload the page.
              </Typography>
              <Button variant="contained" onClick={() => window.location.reload()}>
                Reload
              </Button>
            </>
          ) : (
            <Button variant="contained" onClick={() => this.retry()}>
              Retry
            </Button>
          )}
        </Box>
      );
    }
    return this.props.children;
  }
}
