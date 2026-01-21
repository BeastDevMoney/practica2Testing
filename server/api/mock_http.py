from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple, List

@dataclass
class Request:
    method: str
    path: str
    query: Dict[str, str] | None = None
    json: Any | None = None

@dataclass
class Response:
    status: int
    json: Any = None

Handler = Callable[[Request, Dict[str, str]], Response]

class MockHttpServer:
    def __init__(self):
        self._routes: List[Tuple[str, str, Handler]] = []

    def add_route(self, method: str, path_template: str, handler: Handler) -> None:
        self._routes.append((method.upper(), path_template, handler))

    def handle(self, req: Request) -> Response:
        m = req.method.upper()
        for (rm, tpl, handler) in self._routes:
            if rm != m:
                continue
            params = self._match(tpl, req.path)
            if params is not None:
                return handler(req, params)
        return Response(404, {"error": "route not found", "method": m, "path": req.path})

    @staticmethod
    def _match(tpl: str, path: str) -> Optional[Dict[str, str]]:
        t = [p for p in tpl.strip("/").split("/") if p]
        a = [p for p in path.strip("/").split("/") if p]
        if len(t) != len(a):
            return None
        out: Dict[str, str] = {}
        for tp, ap in zip(t, a):
            if tp.startswith("{") and tp.endswith("}"):
                out[tp[1:-1]] = ap
            elif tp != ap:
                return None
        return out


class MockHttpClient:
    def __init__(self, server: MockHttpServer):
        self.server = server

    def get(self, path: str, query: Dict[str, str] | None = None) -> Response:
        return self.server.handle(Request("GET", path, query=query))

    def post(self, path: str, json: Any | None = None) -> Response:
        return self.server.handle(Request("POST", path, json=json))

    def delete(self, path: str) -> Response:
        return self.server.handle(Request("DELETE", path))
