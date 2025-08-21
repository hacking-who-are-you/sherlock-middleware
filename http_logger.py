import httpx
import time
import json
import re
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class HttpLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, collector_url: str):
        super().__init__(app)
        self.collector_url = collector_url

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()

        request_body_bytes = await request.body()
        request_body_str = request_body_bytes.decode("utf-8", errors="ignore")

        response = await call_next(request)
        process_time = time.time() - start_time

        log_data = {
            "client_ip": request.client.host if request.client else "unknown",
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "request_body": request_body_str,
            "status_code": response.status_code,
            "process_time_ms": int(process_time * 1000),
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.collector_url, json=log_data, timeout=2.0)
        except httpx.RequestError as e:
            print(f"Could not send log to collector: {e}")

        return response
