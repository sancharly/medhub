# ADR-0024: Backend modules are uv workspace members, installed non-editable in the image

## Status

Accepted (2026-11-25, Carlos Santiago Liceras, CR-008 Plan gate, D-B). Proposed the same day by the
Software Architect role (CR-008 Plan stage). The installation option itself was
chosen by the human at the CR-008 Specify gate (D-1 (a), decision D-A); this record states it as an
architecture decision and fixes the details the CR left to the architect. It refines
[ADR-0005](0005-plugin-module-mechanism.md), whose "Neutral" consequence says a plugin is
"build/deploy-time installed (package present in the image)" without saying how.

## Context

ADR-0005 makes a backend module a Python package that registers a `medhub.modules` entry point. It
does not say how the package reaches an environment. The only module, `medhub-dicom-viewer`
(`backend/modules/dicom_viewer/`), was therefore installed nowhere: `backend/pyproject.toml` does not
depend on it, `backend/uv.lock` has no entry for it, and the Dockerfile only copies its source folder
(PRB-048). Discovery found nothing, and the module tests passed only because their `conftest.py`
put the module on `sys.path`.

Forces:

- One lock for everything shipped (SR-028; the image is built only from the frozen lock, as
  RISK-007's "SDK declared and verified in CI" control relies on).
- A module carries its own runtime dependencies (CR-008 D-2): NumPy is needed by the module only.
- Adding the next module should need no new mechanism.
- `medhub-backend` is a virtual uv project (no `[build-system]`): the host package `app` is imported
  from the working directory (`/app` in the image), not installed. A module imports `app.*` the
  same way.
- Build reproducibility (§5.8.5, class B): a built module wheel must not depend on a floating build
  tool.

## Decision

1. **Workspace.** `backend/pyproject.toml` declares `[tool.uv.workspace] members = ["modules/*"]`, a
   `[tool.uv.sources]` entry `{ workspace = true }` per module, and each module in
   `[project] dependencies`. The host stays virtual. One `backend/uv.lock` covers host and modules.
2. **Module-owned dependencies.** A module's `pyproject.toml` lists what it imports (for
   `medhub-dicom-viewer`: `numpy`, `pydicom`); the lock resolves them once for the whole workspace.
3. **Build backend pinned.** A module's `[build-system] requires` names an exact build-backend
   version (`hatchling==1.33.0` today) and its wheel target names its package explicitly
   (`[tool.hatch.build.targets.wheel] packages = ["dicom_viewer"]`; hatchling cannot infer it from
   the project name `medhub-dicom-viewer`). The build backend is build tooling, not SOUP.
4. **Image.** The builder stage runs `uv sync --frozen --no-dev --no-editable`; the runtime stage
   copies the virtual environment only, not `modules/`. The module runs from `site-packages`, so
   the image does not depend on the module source tree at run time.
5. **Development and CI.** `uv sync --frozen` installs workspace members editable (uv's default), so
   a source edit needs no reinstall. Module tests import the installed package; no test puts a
   module on `sys.path`. pytest resolves `app` through `pythonpath = ["."]` in
   `[tool.pytest.ini_options]`, the same root the image uses.
6. **Proof in every environment.** A guard test in the module suite (CI test environment) and a
   step in the Docker Build job (production image) fail unless the entry point is discovered and
   the module and its dependencies import (CR-008 D-6, D-7).

## Consequences

### Positive

- One lock and one resolution for host and modules; a module dependency is reviewed as SOUP like any
  other, and removing a module removes its dependencies from the lock.
- A new module is a new folder under `backend/modules/`, one `[tool.uv.sources]` entry and one
  dependency line; no Dockerfile change.
- The image runs the built wheel, which is what the entry-point metadata describes, so "installed"
  means the same thing in the image as in the CI check.

### Negative

- Workspace members share one resolution: a module cannot pin a dependency version the host or
  another module cannot accept. Accepted: modules are trusted, reviewed code (ADR-0005).
- The development and CI environments run the module editable, the image non-editable. A packaging
  defect that only a built wheel shows (a missing file in the wheel) is caught only by the Docker
  Build job step, not by the module suite.
- The build backend is fetched at image build time; its pin is in the module's `pyproject.toml`,
  outside `backend/uv.lock` and outside the ADR-0020 pin check.

### Neutral

- Installing a module makes it available, not enabled: a system administrator still enables it per
  group (SR-015). Discovery now runs the registry sync at every start-up, which it skipped while no
  module was installed (PRB-075 remains unreachable with a single module; RISK-007).

## Alternatives considered

- **Path dependency** (`[tool.uv.sources] medhub-dicom-viewer = { path = "modules/dicom_viewer" }`,
  CR-008 D-1 (b)). Same result for one module; every new module repeats the source entry and there
  are no shared workspace constraints. Rejected by the human at the Specify gate in favour of the
  workspace.
- **Editable install in the image** (`uv sync --frozen --no-dev`, keeping `COPY modules/`). Works, but
  the image then depends on the source tree being copied next to the environment, and the image no
  longer runs what a wheel would ship. Rejected.
- **Dependencies declared by the host** (NumPy in `backend/pyproject.toml`, CR-008 D-2 alternative).
  Simpler today; the host then carries a dependency only a module uses. Rejected.

## References

- Requirements: SR-016, SR-017 (AC 7), SR-028
- Records: CR-008 (D-1, D-2, D-6, D-7), PRB-048, PRB-075, ADD-015, TASK-233, TASK-236
- Related: ADR-0005, ADR-0020
