import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .utils import generate_s3_key

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

logger = logging.getLogger(__name__)


@dataclass
class S3ResponseMiddleware:
    app: ASGIApp
    s3_bucket_name: str
    s3_client: "S3Client"
    size_threshold: int = int(5.5 * 1024**2)  # 5.5 MB
    key_generator: Callable[..., str] = generate_s3_key
    url_expiry: int = 60 * 60  # 1 hour

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        s3_key = None  # Persist key across header & body messages
        s3_headers = {}  # Persist headers across header & body messages

        async def send_with_s3_response(message: Message):
            nonlocal s3_key
            nonlocal s3_headers

            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                content_length = int(headers.get("content-length", 0))

                if content_length > self.size_threshold:
                    # Set the status to 303 and redirect to the S3 URL
                    logger.debug(
                        "Received response body larger than threshold (%s vs %s), sending to S3.",
                        content_length,
                        self.size_threshold,
                    )
                    s3_key = self.key_generator()
                    s3_headers = {
                        f"Content{key.title()}": headers[f"content-{key}"]
                        for key in [
                            "type",
                            "encoding",
                            "language",
                            "disposition",
                        ]
                        if f"content-{key}" in headers
                    }
                    message["status"] = 303
                    headers["content-length"] = "0"
                    headers["location"] = self.s3_client.generate_presigned_url(
                        "get_object",
                        Params={
                            "Bucket": self.s3_bucket_name,
                            "Key": s3_key,
                        },
                        ExpiresIn=self.url_expiry,
                    )

            elif message["type"] == "http.response.body":
                if s3_key:
                    # Send the response body to S3
                    logger.debug(
                        "Sending response body to s3://%s/%s.",
                        self.s3_bucket_name,
                        s3_key,
                    )
                    self.s3_client.put_object(
                        Bucket=self.s3_bucket_name,
                        Key=s3_key,
                        Body=message["body"],
                        **s3_headers,
                    )
                    message = {"type": "http.response.body", "body": b""}

            await send(message)

        await self.app(scope, receive, send_with_s3_response)
