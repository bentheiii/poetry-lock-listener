# Poetry-Lock-Listener Changelog
## 0.2.4
### Fixed
* if poetry instance cannot be retrieved, the plugin will now disable itself instead of crashing
## 0.2.3
### Added
* the context is now sent to file-style callbacks, same as python hooks
### Fixed
* fixed issues with poetry 2 compatibility
### Internal
* added component tests using docker
## 0.2.2
### Fixed
* project now supports poetry 2.*
## 0.2.0
### Changed
* callback hooks now also accept a `context` parameter, it's empty for now but we're future proofing
### Added
* added a verbosity flag to the plugin, controlled by the `POETRY_LOCK_LISTENER_VERBOSITY` environment variable
### Fixed
* on_changed hooks now handle `input` correctly
* content-hash is now ignored on lockfiles

## 0.1.1
### Added
* setup instructions in the readme
### Fixed
* outputs in the called script are now printed to the console
* the plugin will now ignore projects that don't have a section for it in the pyproject.toml file

## 0.1.0
* Initial release