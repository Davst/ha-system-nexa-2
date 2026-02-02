# Developer Workflow

## Installing the Dev Version (Alpha)

While this project is in Alpha, you may want to test the latest changes from the `dev` branch.

1.  **Add to HACS**: Ensure this repository is added to your HACS Custom Repositories as an "Integration".
2.  **Select Version**:
    - Click on the integration in HACS.
    - Click the three dots (overflow menu) in the top right -> **Redownload**.
    - In the version dropdown, select **Show beta versions** (if applicable) or look for a branch name like `main` or `dev` if available (HACS usually allows installing from specific branches if you select "Master" or similar in the dropdown, depending on HACS version).
    - *Note*: Since we use releases, HACS defaults to the latest Release. To use the bleeding edge code, you usually select the default branch (e.g., `main` or `master`) from the version list.

## Creating a Release

1.  Draft a new Release in GitHub.
2.  Create a new tag (e.g., `v0.0.2`).
3.  Publish the release.
4.  The GitHub Action will automatically:
    - Update `manifest.json` with the version number (e.g., `0.0.2`).
    - Zip the component.
    - Upload the zip to the release.
