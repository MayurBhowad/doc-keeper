import pytest

from document_reader.api import RequestBodyLimitMiddleware, RequestBodyTooLarge


@pytest.mark.anyio
async def test_rejects_oversized_content_length():
    async def app(scope, receive, send):
        pytest.fail("Application should not be called")

    middleware = RequestBodyLimitMiddleware(app, max_body_bytes=4)
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"12345"}

    async def send(message):
        sent.append(message)

    await middleware(
        {
            "type": "http",
            "headers": [(b"content-length", b"5")],
        },
        receive,
        send,
    )

    assert sent[0]["status"] == 413


@pytest.mark.anyio
async def test_rejects_oversized_stream_without_content_length():
    async def app(scope, receive, send):
        await receive()
        await receive()

    middleware = RequestBodyLimitMiddleware(app, max_body_bytes=4)
    sent = []
    chunks = iter([b"123", b"456"])

    async def receive():
        try:
            body = next(chunks)
        except StopIteration:
            return {"type": "http.request", "body": b"", "more_body": False}

        return {"type": "http.request", "body": body, "more_body": True}

    async def send(message):
        sent.append(message)

    await middleware(
        {"type": "http", "headers": []},
        receive,
        send,
    )

    assert sent[0]["status"] == 413


@pytest.mark.anyio
async def test_allows_request_within_limit():
    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"ok",
            }
        )

    middleware = RequestBodyLimitMiddleware(app, max_body_bytes=4)
    sent = []

    async def receive():
        return {
            "type": "http.request",
            "body": b"1234",
            "more_body": False,
        }

    async def send(message):
        sent.append(message)

    await middleware(
        {"type": "http", "headers": []},
        receive,
        send,
    )

    assert sent[0]["status"] == 200


@pytest.mark.anyio
async def test_propagates_oversized_body_after_response_started():
    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )
        await receive()

    middleware = RequestBodyLimitMiddleware(app, max_body_bytes=4)

    async def receive():
        return {
            "type": "http.request",
            "body": b"12345",
            "more_body": False,
        }

    async def send(message):
        pass

    with pytest.raises(RequestBodyTooLarge):
        await middleware(
            {"type": "http", "headers": []},
            receive,
            send,
        )
