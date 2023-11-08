from copy import deepcopy

import uvicorn
from fastapi import FastAPI

_UVICORN_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}

X_MONITE_VERSION_HEADER_NAME = "x-monite-version"
X_MONITE_VERSION_HEADER_VALUE_FORMAT = "%Y-%m-%d"


def get_uvicorn_config(*, is_local: bool = False):
    if not is_local:
        config = deepcopy(_UVICORN_LOGGING_CONFIG)
        config["formatters"]["default"]["()"] = "monite_logger.formatters.JsonFormatter"
        return config
    return _UVICORN_LOGGING_CONFIG


def apply_default_uvicorn_config(app: FastAPI, *, is_local: bool) -> uvicorn.Config:
    return uvicorn.Config(
        app=app,
        proxy_headers=True,
        access_log=False,
        use_colors=False,
        log_config=get_uvicorn_config(is_local=is_local),
    )
