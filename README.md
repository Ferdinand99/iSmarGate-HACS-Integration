# iSmartGate Cloud (Custom HACS Integration)

Unofficial Home Assistant custom integration for controlling iSmartGate through the cloud endpoint pattern used by the Homey community app.

This integration uses:

- `UDI`
- `username`
- `password`

And communicates with:

- `https://<UDI>.isgaccess.com/api.php`

## Important

- This is not an official iSmartGate integration.
- Cloud behavior may change without notice.
- Use at your own risk.

## Features

- Config flow (UI setup)
- Cover entities for enabled doors/gates
- Battery and temperature sensors (when exposed by device)
- Polling via Home Assistant `DataUpdateCoordinator`

## Installation (manual)

1. Copy `custom_components/ismartgate_cloud` to your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Go to Settings -> Devices & Services -> Add Integration.
4. Search for `iSmartGate Cloud`.

## HACS repository structure

This repository is HACS-ready:

- `hacs.json` in repository root
- integration code in `custom_components/ismartgate_cloud`

## GitHub repository setup included

This repository now includes:

- CI validation workflow for Home Assistant and HACS.
- Tag-based release workflow creating `ismartgate_cloud.zip`.
- Issue templates for bugs and feature requests.
- `CODEOWNERS`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `LICENSE`.

### Release process

1. Bump version in `custom_components/ismartgate_cloud/manifest.json`.
2. Update `CHANGELOG.md`.
3. Create and push a git tag (example: `v0.1.1`).
4. GitHub Actions builds a release ZIP and publishes a Release.

## Notes

- If your controller and Home Assistant can reach each other locally, use the built-in iSmartGate/GogoGate2 integration first.
- This custom integration is intended for cloud-based access scenarios.