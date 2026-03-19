# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 19-03-2026

### Added

- Added complete GitHub repository setup:
	- CI validation workflow (`hassfest` + HACS validation)
	- issue templates and pull request template
	- CODEOWNERS, CONTRIBUTING, LICENSE, `.gitignore`, `.editorconfig`, `.gitattributes`
- Added automatic release workflow on version tags (`v*`) that builds and publishes zip artifact.
- Added automatic tag-and-release workflow triggered after successful `Validate` runs on `main`.

### Changed

- Improved cloud API parsing for telemetry by checking multiple field variants for temperature and battery/voltage values.
- Improved float parsing to support comma decimals (for example `21,5`).

### Fixed

- Fixed import error in cover platform by using integration constant `CONF_UDI` from local constants module.
- Fixed Home Assistant manifest validation issues:
	- added required `documentation` and `issue_tracker`
	- sorted manifest keys according to hassfest requirements
- Fixed HACS validation issues:
	- corrected `hacs.json` schema (removed unsupported `domains` key)
	- corrected HACS action ignore format to space-separated values
- Fixed sensor device linking: battery and temperature sensors now attach to the same Home Assistant device as the garage cover.

## [0.1.0] - 19-03-2026

- Initial release of iSmartGate Cloud custom integration.
- Added config flow (UDI, username, password, polling interval).
- Added cover entities for enabled doors/gates.
- Added battery and temperature sensors when available.
- Added HACS metadata and translations.
