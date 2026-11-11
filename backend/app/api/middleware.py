"""Pure-ASGI request-size guard."""
from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class MaxBodySizeMiddleware:
    """Reject oversized request bodies on one path BEFORE the multipart parser spools them to disk.

    Without this, Starlette copies the entire upload to a temp file before the route runs, so a
    route-level size check alone cannot stop a huge upload from filling the disk. Checks the
    Content-Length header up front, and counts bytes as they arrive for chunked / lying clients.
    """

    def __init__(self, app: ASGIApp, *, path: str, max_bytes: int, message: str):
        self.app = app
        self.path = path
        self.max_bytes = max_bytes
        self.message = message

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] != self.path:
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None:
            try:
                too_big = int(declared) > self.max_bytes
            except ValueError:
                too_big = False  # unparseable header: fall through to byte counting
            if too_big:
                response = JSONResponse({"detail": self.message}, status_code=413, headers={"Connection": "close"})
                await response(scope, receive, send)
                return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    # FastAPI re-raises HTTPExceptions thrown while parsing the body, so this becomes a clean 413.
                    raise HTTPException(status_code=413, detail=self.message)
            return message

        await self.app(scope, limited_receive, send)
