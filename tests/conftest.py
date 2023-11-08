import uuid

import pytest
from monite_common.schemas.auth_data import MoniteAuthData


@pytest.fixture()
def partner_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture()
def project_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture()
def entity_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture()
def auth_data(partner_id: str, project_id: str, entity_id: str) -> MoniteAuthData:
    return MoniteAuthData.parse_obj(
        {
            "partner": {"id": partner_id},
            "project": {"id": project_id},
            "entity": {"id": entity_id},
        },
    )
