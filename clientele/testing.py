from __future__ import annotations

import json as json_

from clientele.api import client as api_client
from clientele.http import fake_backend


def configure_client_for_testing(
    client: api_client.APIClient,
) -> fake_backend.FakeHTTPBackend:
    """Function that provides a FakeHTTPBackend for testing.

    This function takes an APIClient instance and
    configures it to use a FakeHTTPBackend.

    The function returns the FakeHTTPBackend instance so you can queue responses
    in your test.

    Args:
        client: An APIClient instance to configure with the fake backend.
    Returns:
        A FakeHTTPBackend instance configured with the client.

    """

    # Create the fake backend
    backend = fake_backend.FakeHTTPBackend()

    # Configure the client to use the fake backend
    config = client.config
    config.http_backend = backend
    client.configure(config=config)

    # Return the backend
    return backend


class ResponseFactory:
    """Factory for creating common HTTP responses.

    Simplifies creating mock responses for testing by providing
    convenience methods for common HTTP status codes.

    Example:
        >>> from clientele.testing import ResponseFactory
        >>> backend.queue_response("/users", ResponseFactory.json([{"id": 1}]))
        >>> backend.queue_response("/users/99", ResponseFactory.not_found())
    """

    @staticmethod
    def json(
        data: object,
        status: int = 200,
        headers: dict[str, str] | None = {},
    ) -> fake_backend.response.Response:
        """Create a JSON response.

        Args:
            data: Python object to serialize as JSON body
            status: HTTP status code (default: 200)
            headers: Additional headers (Content-Type auto-added)
        """
        content = json_.dumps(data).encode("utf-8")
        default_headers = {"content-type": "application/json", **headers}
        return fake_backend.response.Response(
            status_code=status,
            content=content,
            headers=default_headers,
        )

    @staticmethod
    def text(
        body: str,
        status: int = 200,
        headers: dict[str, str] | None = {},
    ) -> fake_backend.response.Response:
        """Create a plain text response."""
        default_headers = {"content-type": "text/plain", **headers}
        return fake_backend.response.Response(
            status_code=status,
            content=body.encode("utf-8"),
            headers=default_headers,
        )

    @staticmethod
    def empty(status: int = 204) -> fake_backend.response.Response:
        """Create an empty response (default: 204 No Content)."""
        return fake_backend.response.Response(
            status_code=status,
            content=b"",
            headers={},
        )

    @staticmethod
    def ok(data: object | None = None) -> fake_backend.response.Response:
        """200 OK with optional JSON body."""
        if not data:
            return ResponseFactory.empty(status=200)
        return ResponseFactory.json(data, status=200)

    @staticmethod
    def created(data: object | None = None) -> fake_backend.response.Response:
        """201 Created with optional JSON body."""
        if not data:
            return ResponseFactory.empty(status=201)
        return ResponseFactory.json(data, status=201)

    @staticmethod
    def accepted(data: object | None = None) -> fake_backend.response.Response:
        """202 Accepted with optional JSON body."""
        if not data:
            return ResponseFactory.empty(status=202)
        return ResponseFactory.json(data, status=202)

    @staticmethod
    def bad_request(message: str = "Bad Request") -> fake_backend.response.Response:
        """400 Bad Request."""
        return ResponseFactory.json({"error": message}, status=400)

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> fake_backend.response.Response:
        """401 Unauthorized."""
        return ResponseFactory.json({"error": message}, status=401)

    @staticmethod
    def forbidden(message: str = "Forbidden") -> fake_backend.response.Response:
        """403 Forbidden."""
        return ResponseFactory.json({"error": message}, status=403)

    @staticmethod
    def not_found(message: str = "Not Found") -> fake_backend.response.Response:
        """404 Not Found."""
        return ResponseFactory.json({"error": message}, status=404)

    @staticmethod
    def conflict(message: str = "Conflict") -> fake_backend.response.Response:
        """409 Conflict."""
        return ResponseFactory.json({"error": message}, status=409)

    @staticmethod
    def unprocessable_entity(
        errors: dict[str, list[str]] | None = None,
    ) -> fake_backend.response.Response:
        """422 Unprocessable Entity with validation errors."""
        body: dict[str, object] = {"error": "Unprocessable Entity"}
        if errors:
            body["errors"] = errors
        return ResponseFactory.json(body, status=422)

    @staticmethod
    def server_error(message: str = "Internal Server Error") -> fake_backend.response.Response:
        """500 Internal Server Error."""
        return ResponseFactory.json({"error": message}, status=500)

    @staticmethod
    def service_unavailable(message: str = "Service Unavailable") -> fake_backend.response.Response:
        """503 Service Unavailable."""
        return ResponseFactory.json({"error": message}, status=503)


class NetworkError:
    """Factory for network error simulation.

    These errors simulate network-level failures that occur
    before receiving an HTTP response.

    Example:
        >>> from clientele.testing import NetworkError
        >>> backend.queue_error("/users", NetworkError.timeout())
    """

    @staticmethod
    def timeout(message: str = "Request timed out") -> TimeoutError:
        """Simulate a request timeout."""
        return TimeoutError(message)

    @staticmethod
    def connection_refused(message: str = "Connection refused") -> ConnectionRefusedError:
        """Simulate connection refused by server."""
        return ConnectionRefusedError(message)

    @staticmethod
    def connection_reset(message: str = "Connection reset by peer") -> ConnectionResetError:
        """Simulate connection reset during request."""
        return ConnectionResetError(message)

    @staticmethod
    def dns_failure(host: str = "unknown") -> OSError:
        """Simulate DNS resolution failure."""
        return OSError(f"Failed to resolve hostname: {host}")
