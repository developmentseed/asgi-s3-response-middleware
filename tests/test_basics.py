def test_version():
    from asgi_s3_response_middleware import __version__

    assert isinstance(__version__, str)
    assert len(__version__.split(".")) == 3
