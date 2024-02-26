# Changelog

All notable changes to this project will be documented in this file.
Please follow [the Keep a Changelog standard](https://keepachangelog.com/en/1.0.0/).

## [0.2.0]

### Changed

* Version header now parsed using `fromisoformat` for performance improvment

### Added

* `lifespan` parameter to the `HeaderRoutingFastAPI` class to support FastAPI's `on_event` lifecycle events migration
* default value to version header for endpoints in openapi

## [0.1.1]

### Added

* added `async_exit_stack` parameter to `solve_dependencies` in the middleware to support fastapi's API

## [0.1.0]

### Changed

* `HeaderRoutingFastAPI.add_header_versioned_routers` now returns the list of added routes

## [0.0.6]

### Added

* initial release
