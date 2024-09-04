<div align="center">
<!-- Consider using a logo image:
  <img width="500" alt="logo-description" src="https://github.com/developmentseed/asgi_s3_response_middleware/assets/10407788/fc69e5ae-4ab7-491f-8c20-6b9e1372b4c6">
-->
  <h3 style="font-family: monospace">ASGI S3 Response Middleware</h3>
  <p align="center">Middleware to spill large responses over to S3.</p>
</div>

---

<!-- **Documentation**: <a href="TODO..." target="_blank">TODO...</a> -->

**Source Code**: <a href="https://github.com/developmentseed/asgi-s3-response-middleware" target="_blank">https://github.com/developmentseed/asgi-s3-response-middleware</a>

---

## Usage

An ASGI middleware class to automatically push repsonses S3 and instead return a 303 redirect to the object on S3.

This can be useful to avoid hitting limits on the size of API response bodies, such as when working around [AWS Lambda's 6MB response limit](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).

### Example

```py
import uuid
import boto3
from fastapi import FastAPI
from asgi_s3_response_middleware import S3ResponseMiddleware

s3_client = boto3.client('s3')

app = FastAPI()

app.add_middleware(
    S3ResponseMiddleware,
    s3_bucket_name='my-example-bucket',
    s3_client=s3_client,
    key_generator=lambda: f"responses/{uuid.uuid4()}",
    size_threshold=2 * 1024**2,  # 2MB
    url_expiry=30,  # 30 seconds
)
```

## Development

### Releases

Releases are managed via CICD workflow, as described in the [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/). To create a new release:

1. Update the version in `src/asgi_s3_response_middleware/__init__.py` following appropriate [Semantic Versioning convention](https://semver.org/).
1. Push a tagged commit to `main`, with the tag matching the package's new version number.

> [!NOTE]  
> This package makes use of Github's [automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes). These can be later augmented if one sees fit.
