# Poetry-Lock-Listener Changelog
## 0.2.1
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