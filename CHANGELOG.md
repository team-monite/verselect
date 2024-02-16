# Changelog

All notable changes to this project will be documented in this file.
Please follow [the Keep a Changelog standard](https://keepachangelog.com/en/1.0.0/).


## [0.2.0] - 2024-01-15

### Changed

* Version header now parsed using `fromisoformat` for performance improvment


## [0.1.2] - 2024-02-12

### Added

* added `lifespan` parameter to the `HeaderRoutingFastAPI` class to support FastAPI's `on_event` lifecycle events migration


## [0.1.1] - 2024-01-15

### Added

* added `async_exit_stack` parameter to `solve_dependencies` in the middleware to support fastapi's API

## [0.1.0] - 2023-12-01

### Changed

* `HeaderRoutingFastAPI.add_header_versioned_routers` now returns the list of added routes

## [0.0.6] - 2023-11-30

### Added

* initial release
