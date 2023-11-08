from tests._resources.app_that_raises_errors import client


def test__business_logic_error():
    resp = client.post("/v1/raise_business_logic_error")
    assert resp.status_code == 409
    assert resp.json()["error"]["message"] == "this logic is against business"


def test__regular_error():
    resp = client.post("/v1/raise_regular_exception")
    assert resp.status_code == 500
    assert resp.json()["error"]["message"] == "Server Error"


def test__internal_request_error():
    resp = client.post("/v1/raise_internal_request_error")
    assert resp.status_code == 500
    assert resp.json()["error"]["message"] == "Internal server error."


def test__http_validation_error():
    resp = client.post("/v1/raise_http_validation_error")
    assert resp.status_code == 422
    assert resp.json() == "HTTP Validation Error"


def test__external_request_error():
    resp = client.post("/v1/raise_external_request_error")
    assert resp.status_code == 405
    assert resp.json() == {"error": {"message": "Oh my external request error"}}


def test__monite_response_error__with_propagation():
    resp = client.post("/v1/raise_monite_response_error_with_propagation")
    assert resp.status_code == 409
    assert resp.json() == {"error": {"message": "hewwo"}}


def test__monite_response_error_default__should_hide_error_message():
    resp = client.post("/v1/raise_monite_response_error_default")
    assert resp.status_code == 500
    assert resp.json() == {"error": {"message": "Server Error"}}


def test__raise_monite_response_error_default__with_propagation():
    resp = client.post("/v1/raise_monite_response_error_default_with_propagation")
    assert resp.status_code == 409
    assert resp.json() == {"error": {"message": "hewwo"}}


def test__raise_monite_response_error_default__with_propagation_and_non_str_message__message_shouldnt_be_str():
    resp = client.post("/v1/raise_monite_response_error_default_with_propagation_and_non_str_message")
    assert resp.status_code == 409
    assert resp.json() == {"error": {"message": {"hewwo": ["world"]}}}


def test__validation_error_during_request_handling():
    resp = client.post("/v1/raise_pydantic_validation_error")
    assert resp.status_code == 500
    assert resp.json() == {"error": {"message": "Response validation error"}}


def test__request_validation_error__wrong_name__error():
    resp = client.post("/v1/number", json={"numero": "hewwo"})
    assert resp.status_code == 422
    assert resp.json() == {
        "detail": [{"loc": ["body", "number"], "msg": "field required", "type": "value_error.missing"}],
    }


def test__request_validation_error__wrong_http_url__should_raise_validation_error():
    resp = client.post("/v1/raise_http_url_error", json={"https_url": "http://google.com"})
    assert resp.status_code == 422
    assert resp.json() == {
        "detail": [
            {
                "loc": ["body", "https_url"],
                "msg": "URL scheme not permitted",
                "type": "value_error.url.scheme",
                "ctx": {"allowed_schemes": ["https"]},
            },
        ],
    }
