# Developer Workflow

## Installing the Dev Version (Alpha)

While this project is in Alpha, you may want to test the latest changes from the `main` branch.

1.  **Add to HACS**: Ensure this repository is added to your HACS Custom Repositories as an "Integration".
2.  **Select Version**:
    - Click on the integration in HACS.
    - Click the three dots (overflow menu) in the top right -> **Redownload**.
    - Since we have releases, HACS will default to the latest release (e.g., `v0.0.1`).

## Released Versions

We use an **automated release workflow**:

1.  **Push to `main`**: Any push to the `main` branch triggers the release workflow.
2.  **Auto-Versioning**: The workflow automatically:
    - Finds the latest tag (e.g., `v0.0.1`).
    - Increments the patch version (e.g., to `v0.0.2`).
    - Updates `manifest.json` inside the release artifact.
    - Creates a new GitHub Release and Tag.
    - Uploads the zip file for HACS.

**Do not manually create releases** unless you need to override this behavior (e.g., for major/minor bumps).
