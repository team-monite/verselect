import pytest
import uvicorn

from verselect.apps import HeaderRoutingFastAPI
from verselect.configs import apply_default_uvicorn_config, get_uvicorn_config


def test__uvicorn_config_can_be_called_without_errors_with_default_prod_config():
    uvicorn.Config(
        app=HeaderRoutingFastAPI(),
        proxy_headers=True,
        log_config=get_uvicorn_config(is_local=False),
    )


@pytest.mark.parametrize("is_local", [True, False])
def test__uvicorn_config_is_applied_with_correct_default_settings(is_local: bool):
    cfg = apply_default_uvicorn_config(HeaderRoutingFastAPI(), is_local=is_local)
    assert cfg.proxy_headers is True
    assert cfg.access_log is False
    assert cfg.use_colors is False
    assert cfg.log_config == get_uvicorn_config(is_local=is_local)


def test__uvicorn_config_can_be_called_without_errors_with_default_local_config():
    uvicorn.Config(
        app=HeaderRoutingFastAPI(),
        proxy_headers=True,
        log_config=get_uvicorn_config(is_local=True),
    )
