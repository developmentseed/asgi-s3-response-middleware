import os

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_s3.client import S3Client
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from asgi_s3_response_middleware import S3ResponseMiddleware


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    """
    Return a mocked S3 client
    """
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def test_bucket(s3: S3Client) -> str:
    bucket_name = "bb1"
    s3.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def app_with_s3_middleware(s3: S3Client, test_bucket: str):
    async def echo(request):
        body = await request.json()
        return PlainTextResponse(body)

    app = Starlette(routes=[Route("/echo", echo, methods=["POST"])])

    app.add_middleware(
        S3ResponseMiddleware,
        s3_bucket_name=test_bucket,
        s3_client=s3,
    )

    return app


def test_middleware_s3_redirect_large_request(app_with_s3_middleware, test_bucket: str):
    client = TestClient(app_with_s3_middleware)
    body = "abc" * 2 * 1024**2  # 6 MB
    response = client.post("/echo", follow_redirects=False, json=body)

    # Assert that the response headers include the custom headers
    assert "Location" in response.headers
    assert response.headers["Location"].startswith(
        f"https://{test_bucket}.s3.amazonaws.com/"
    )
    assert response.status_code == 303
    assert response.text == ""


def test_middleware_s3_below_threshold(app_with_s3_middleware):
    client = TestClient(app_with_s3_middleware)
    body = "abc123"
    response = client.post("/echo", follow_redirects=False, json=body)

    # Assert that the response headers include the custom headers
    assert "Location" not in response.headers
    assert response.status_code == 200
    assert response.text == body
