import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentic_shared.core.domain_errors import (
    BadRequestError,
    ConflictError,
    DomainError,
    NotFoundError,
)
from agentic_shared.frameworks.fastapi.domain_errors import register_domain_error_handlers


def _client_for_errors() -> TestClient:
    app = FastAPI()
    register_domain_error_handlers(app)

    @app.get("/not-found")
    def _not_found() -> None:
        raise NotFoundError("Resource missing")

    @app.get("/conflict")
    def _conflict() -> None:
        raise ConflictError("Already exists")

    @app.get("/bad-request")
    def _bad_request() -> None:
        raise BadRequestError("Invalid input")

    @app.get("/domain")
    def _domain() -> None:
        raise DomainError("Generic domain failure")

    return TestClient(app)


class TestDomainErrorHandlers(unittest.TestCase):
    def test_not_found_maps_to_404(self) -> None:
        # Act
        response = _client_for_errors().get("/not-found")

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Resource missing"})

    def test_conflict_maps_to_409(self) -> None:
        # Act
        response = _client_for_errors().get("/conflict")

        # Assert
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": "Already exists"})

    def test_bad_request_maps_to_400(self) -> None:
        # Act
        response = _client_for_errors().get("/bad-request")

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Invalid input"})

    def test_generic_domain_error_maps_to_400(self) -> None:
        # Act
        response = _client_for_errors().get("/domain")

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Generic domain failure"})


if __name__ == "__main__":
    unittest.main()
