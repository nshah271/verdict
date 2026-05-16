# Releasing verdict (PyPI package `myverdict`)

This is the publish runbook. The PyPI name is `myverdict` because the older `verdict-ai` slot was taken before we shipped.

## First-time bootstrap (one time only)

PyPI's trusted publishing flow needs the project to already exist before it can grant a GitHub repo permission to push to it. So the very first release goes out from a laptop with an API token, and every release after that goes out automatically via the GitHub Actions workflow.

1. Make a PyPI account if you don't have one, then create an API token at https://pypi.org/manage/account/token/ scoped to "Entire account" for this one upload.
2. Build and upload from a clean clone:
   ```bash
   git checkout main && git pull
   git tag v0.1.0
   pip install --upgrade build twine
   python -m build
   twine upload dist/*
   # username: __token__
   # password: <paste the token>
   ```
3. Confirm the package shows up at https://pypi.org/project/myverdict/.
4. On PyPI, go to the project's **Settings -> Publishing** and add a trusted publisher:
   - Owner: `nshah271`
   - Repository: `verdict`
   - Workflow filename: `release.yml`
   - Environment name: `pypi`
5. Push the tag so the team's git history matches:
   ```bash
   git push --tags
   ```

After step 4, no API tokens are stored anywhere; future releases are signed by GitHub's OIDC token at publish time.

## Cutting a new release (after bootstrap)

1. Decide the new version and update `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```
2. Commit the bump on `main` (or via a small PR):
   ```bash
   git commit -am "bump version to 0.2.0"
   git push
   ```
3. Tag and push the tag. The tag must match the `pyproject.toml` version exactly (the release workflow checks this):
   ```bash
   git tag v0.2.0
   git push --tags
   ```
4. Watch the Release workflow at `https://github.com/nshah271/verdict/actions/workflows/release.yml`. It builds, then publishes via trusted publishing.
5. Verify the new version at `https://pypi.org/project/myverdict/`.

## Version numbering

We use semver:
- patch (`0.1.0 -> 0.1.1`) for bugfixes and FP cleanups
- minor (`0.1.0 -> 0.2.0`) for new checks or CLI features
- major (`0.X -> 1.0`) when we promise a stable check API

`0.X` versions are still pre-1.0, so we'll occasionally make breaking changes in minor bumps. The CHANGELOG (when it exists) will call them out.

## If something goes wrong

- **Workflow fails on "Verify tag matches pyproject version":** you tagged before updating `pyproject.toml`. Fix the file, commit, delete the tag both locally and on remote (`git tag -d v0.2.0 && git push origin :refs/tags/v0.2.0`), then re-tag.
- **`pypi-publish` step fails with "no trusted publisher configured":** the bootstrap step 4 didn't happen, or the workflow filename / env name doesn't match what's registered on PyPI.
- **Need to yank a bad release:** `pip install twine && twine yank myverdict==0.2.0 -m "reason"` (requires an API token). Yanking is not deletion; it just hides the version from `pip install` defaults.
