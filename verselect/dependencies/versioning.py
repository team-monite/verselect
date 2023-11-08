from datetime import date

from fastapi import Header


def get_predefined_monite_version_header(version: str):
    def get_monite_version(x_monite_version: date = Header(..., examples=[version])) -> None:  # noqa: B008
        raise NotImplementedError

    return get_monite_version
