import pytest
import sys
from flask.testing import FlaskClient
from unittest.mock import MagicMock, patch

path = "flask_app"
if path not in sys.path:
    sys.path.append(path)
from flask_app.flask_app import create_app


@pytest.fixture
def mock_redis():
    return MagicMock()


@pytest.fixture
def client(mock_redis):
    with patch("flask_app.flask_app.redis.Redis", return_value=mock_redis):
        app = create_app(redis_client=mock_redis)
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client


def test_input_view(client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<title>Image Selection</title>" in response.data


def test_logging_status_initial(client: FlaskClient):
    response = client.post("/logging_status")
    assert response.status_code == 200
    assert b"logging is enabled" in response.data


def test_disable_logging(client: FlaskClient):
    response = client.post("/disable_logging")
    assert response.status_code == 200
    response = client.post("/logging_status")
    assert b"logging is disabled" in response.data


def test_enable_logging(client: FlaskClient):
    client.post("/disable_logging")
    response = client.post("/enable_logging")
    assert response.status_code == 200
    response = client.post("/logging_status")
    assert b"logging is enabled" in response.data


def test_log_selection(client: FlaskClient, mock_redis: MagicMock):
    client.post("/enable_logging")
    data = {
        "clicked_image": "image1.jpg",
        "not_clicked_image": "image2.jpg",
        "timestamp": "2024-08-02T12:34:56",
    }
    response = client.post("/log_selection", json=data)
    assert response.status_code == 200
    assert b"success" in response.data

    # Check if Redis method was called correctly
    mock_redis.hincrby.assert_called_once_with("likes", "image1", 1)
