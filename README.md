# Poetry Lock Listener
This is a poetry plugin that executes a script whenever a project dependency is changed.

## Installation
```bash
poetry self add poetry-lock-listener
```

in the toml file:
```toml
[tool.poetry_lock_listener]
package_changed_hook="path.to.file:main"
```