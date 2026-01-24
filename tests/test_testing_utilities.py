"""Tests for testing utilities: ResponseFactory and NetworkError simulation."""

import pytest

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.http import fake_backend
from clientele.testing import NetworkError, ResponseFactory


def test_json_response():
    response = ResponseFactory.json({"key": "value"})

    assert response.status_code == 200
    assert response.json() == {"key": "value"}
    assert response.headers["content-type"] == "application/json"


def test_json_with_custom_status():
    response = ResponseFactory.json({"data": [1, 2, 3]}, status=201)

    assert response.status_code == 201
    assert response.json() == {"data": [1, 2, 3]}


def test_json_with_custom_headers():
    response = ResponseFactory.json(
        {"result": "ok"},
        headers={"X-Custom-Header": "custom-value"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["X-Custom-Header"] == "custom-value"


def test_text_response():
    response = ResponseFactory.text("Hello, World!")

    assert response.status_code == 200
    assert response.text == "Hello, World!"
    assert response.headers["content-type"] == "text/plain"


def test_text_with_custom_status():
    response = ResponseFactory.text("Accepted", status=202)

    assert response.status_code == 202
    assert response.text == "Accepted"


def test_empty_response():
    response = ResponseFactory.empty()

    assert response.status_code == 204
    assert response.content == b""


def test_empty_response_with_custom_status():
    response = ResponseFactory.empty(status=200)

    assert response.status_code == 200
    assert response.content == b""


def test_ok_with_data():
    response = ResponseFactory.ok({"success": True})

    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_ok_without_data():
    response = ResponseFactory.ok()

    assert response.status_code == 200
    assert response.content == b""


def test_created():
    response = ResponseFactory.created({"id": 42})

    assert response.status_code == 201
    assert response.json() == {"id": 42}


def test_created_without_data():
    response = ResponseFactory.created()

    assert response.status_code == 201
    assert response.content == b""


def test_accepted():
    response = ResponseFactory.accepted({"job_id": "abc123"})

    assert response.status_code == 202
    assert response.json() == {"job_id": "abc123"}


def test_bad_request():
    response = ResponseFactory.bad_request()

    assert response.status_code == 400
    assert response.json() == {"error": "Bad Request"}


def test_bad_request_custom_message():
    response = ResponseFactory.bad_request("Invalid input")

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid input"}


def test_unauthorized():
    response = ResponseFactory.unauthorized()

    assert response.status_code == 401
    assert response.json() == {"error": "Unauthorized"}


def test_forbidden():
    response = ResponseFactory.forbidden()

    assert response.status_code == 403
    assert response.json() == {"error": "Forbidden"}


def test_not_found():
    response = ResponseFactory.not_found()

    assert response.status_code == 404
    assert response.json() == {"error": "Not Found"}


def test_not_found_custom_message():
    response = ResponseFactory.not_found("User not found")

    assert response.status_code == 404
    assert response.json() == {"error": "User not found"}


def test_conflict():
    response = ResponseFactory.conflict()

    assert response.status_code == 409
    assert response.json() == {"error": "Conflict"}


def test_unprocessable_entity_basic():
    response = ResponseFactory.unprocessable_entity()

    assert response.status_code == 422
    assert response.json() == {"error": "Unprocessable Entity"}


def test_unprocessable_entity_with_errors():
    errors = {"email": ["Invalid email format"], "name": ["Required"]}
    response = ResponseFactory.unprocessable_entity(errors=errors)

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Unprocessable Entity"
    assert body["errors"] == errors


def test_server_error():
    response = ResponseFactory.server_error()

    assert response.status_code == 500
    assert response.json() == {"error": "Internal Server Error"}


def test_service_unavailable():
    response = ResponseFactory.service_unavailable()

    assert response.status_code == 503
    assert response.json() == {"error": "Service Unavailable"}


def test_queue_timeout():
    """Test queuing and raising a timeout error."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkError.timeout())

    with pytest.raises(TimeoutError, match="Request timed out"):
        get_users()

    # Verify the error was captured in requests
    assert len(backend.requests) == 1
    assert "error" in backend.requests[0]

    client.close()


def test_queue_connection_refused():
    """Test queuing and raising a connection refused error."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkError.connection_refused())

    with pytest.raises(ConnectionRefusedError):
        get_users()

    client.close()


def test_queue_connection_reset():
    """Test queuing and raising a connection reset error."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkError.connection_reset())

    with pytest.raises(ConnectionResetError, match="Connection reset by peer"):
        get_users()

    client.close()


def test_queue_dns_failure():
    """Test queuing and raising a DNS resolution failure."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkError.dns_failure("api.example.com"))

    with pytest.raises(OSError, match="Failed to resolve hostname"):
        get_users()

    client.close()


def test_error_takes_priority_over_response():
    """Test that queued errors take priority over queued responses."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/resource")
    def get_resource(result: dict) -> dict:
        return result

    backend.queue_error("/resource", NetworkError.timeout())
    backend.queue_response("/resource", ResponseFactory.ok({"data": "value"}))

    # Error should be raised first
    with pytest.raises(TimeoutError):
        get_resource()

    # Now the response should be returned
    result = get_resource()
    assert result == {"data": "value"}

    client.close()


def test_error_consumed_fifo():
    """Test that errors are consumed in FIFO order."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/resource")
    def get_resource(result: dict) -> dict:
        return result

    backend.queue_error("/resource", NetworkError.timeout())
    backend.queue_error("/resource", NetworkError.connection_refused())
    backend.queue_response("/resource", ResponseFactory.ok({"success": True}))

    with pytest.raises(TimeoutError):
        get_resource()

    with pytest.raises(ConnectionRefusedError):
        get_resource()

    result = get_resource()
    assert result == {"success": True}

    client.close()


@pytest.mark.asyncio
async def test_async_error():
    """Test that errors work with async requests."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    async def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkError.timeout())

    with pytest.raises(TimeoutError):
        await get_users()

    await client.aclose()


def test_reset_clears_errors():
    """Test that reset() clears queued errors."""
    backend = fake_backend.FakeHTTPBackend()

    backend.queue_error("/resource", NetworkError.timeout())
    assert len(backend._error_map["/resource"]) == 1

    backend.reset()

    assert len(backend._error_map) == 0
