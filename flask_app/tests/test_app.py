import pytest
from flask import Flask
import flask_app.flask_app as app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_redirect(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.location == "http://localhost/input"


def test_input_view(client):
    response = client.get("/input")
    assert response.status_code == 200
    assert b"Enter something" in response.data


def test_output_view_no_data(client):
    response = client.get("/output")
    assert response.status_code == 200
    assert b"No input processed yet" in response.data


def test_logging_status_initial(client):
    response = client.post("/logging_status")
    assert response.status_code == 200
    assert b"logging is enabled" in response.data


def test_disable_logging(client):
    response = client.post("/disable_logging")
    assert response.status_code == 200
    response = client.post("/logging_status")
    assert b"logging is disabled" in response.data


def test_enable_logging(client):
    client.post("/disable_logging")
    response = client.post("/enable_logging")
    assert response.status_code == 200
    response = client.post("/logging_status")
    assert b"logging is enabled" in response.data


def test_log_selection(client):
    client.post("/enable_logging")
    data = {
        "clicked_image": "image1.jpg",
        "not_clicked_image": "image2.jpg",
        "timestamp": "2024-08-02T12:34:56",
    }
    response = client.post("/log_selection", json=data)
    assert response.status_code == 200
    assert b"success" in response.data
