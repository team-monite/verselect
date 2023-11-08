import pytest
from monite_common.schemas.auth_data import MoniteAuthData

from tests._resources import app_for_testing_dependencies

get_auth_data_url_parametrize = pytest.mark.parametrize("url", ["/v1/get_auth_data_optional", "/v1/get_auth_data"])
get_entity_id_url_parametrize = pytest.mark.parametrize("url", ["/v1/get_entity_id_optional", "/v1/get_entity_id"])


def test__get_auth_data__auth_data_not_passed__error():
    response = app_for_testing_dependencies.client.get("/v1/get_auth_data")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [{"loc": ["header", "x-monite-auth-data"], "msg": "field required", "type": "value_error.missing"}],
    }


def test__get_auth_data__auth_data_passed(auth_data: MoniteAuthData):
    response = app_for_testing_dependencies.client.get(
        "/v1/get_auth_data",
        headers={"x-monite-auth-data": auth_data.json()},
    )
    assert response.status_code == 200
    assert response.json() == {
        "project": {"id": str(auth_data.project_id)},
        "partner": {"id": str(auth_data.partner_id)},
        "entity": {"id": str(auth_data.entity_id)},
        "entity_user": None,
    }


def test__get_auth_data_optional__auth_data_not_passed__empty_response():
    response = app_for_testing_dependencies.client.get("/v1/get_auth_data_optional")
    assert response.status_code == 200
    assert response.json() == "No auth data"


def test__get_auth_data_optional__auth_data_passed(auth_data: MoniteAuthData):
    response = app_for_testing_dependencies.client.get(
        "/v1/get_auth_data",
        headers={"x-monite-auth-data": auth_data.json()},
    )
    assert response.status_code == 200
    assert response.json() == {
        "project": {"id": str(auth_data.project_id)},
        "partner": {"id": str(auth_data.partner_id)},
        "entity": {"id": str(auth_data.entity_id)},
        "entity_user": None,
    }


@pytest.mark.parametrize("auth_data_with_wrong_structure", ["{}", "[]", "null", "123", "true", "false"])
@get_auth_data_url_parametrize
def test__get_auth_data__auth_data_is_wrong_structure__error(url: str, auth_data_with_wrong_structure: str):
    response = app_for_testing_dependencies.client.get(
        url,
        headers={"x-monite-auth-data": auth_data_with_wrong_structure},
    )
    assert response.status_code == 422
    assert response.json() == [
        {"loc": ["project"], "msg": "field required", "type": "value_error.missing"},
        {"loc": ["partner"], "msg": "field required", "type": "value_error.missing"},
    ]


@get_auth_data_url_parametrize
def test__get_auth_data__auth_data_is_not_json__error(url: str):
    response = app_for_testing_dependencies.client.get(url, headers={"x-monite-auth-data": "Definitely not json"})
    assert response.status_code == 400
    assert response.json() == {"error": {"message": "x-monite-auth-data should be a json string"}}


@get_entity_id_url_parametrize
def test__get_entity_id__auth_data_is_wrong_type__error(url: str):
    response = app_for_testing_dependencies.client.get(url, headers={"x-monite-entity-id": "Not uuid"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {"loc": ["header", "x-monite-entity-id"], "msg": "value is not a valid uuid", "type": "type_error.uuid"},
        ],
    }


def test__get_entity_id__entity_id_not_passed__error():
    response = app_for_testing_dependencies.client.get("/v1/get_entity_id")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [{"loc": ["header", "x-monite-entity-id"], "msg": "field required", "type": "value_error.missing"}],
    }


def test__get_entity_id_optional__entity_id_not_passed__empty_response():
    response = app_for_testing_dependencies.client.get("/v1/get_entity_id_optional")
    assert response.status_code == 200
    assert response.json() == "No entity id"


@get_entity_id_url_parametrize
def test__get_entity_id__entity_id_passed(url: str, entity_id: str):
    response = app_for_testing_dependencies.client.get(url, headers={"x-monite-entity-id": entity_id})
    assert response.status_code == 200
    assert response.json() == entity_id
