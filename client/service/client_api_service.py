from server.api.mock_http import MockHttpClient

class ClientApiService:
    def __init__(self, http: MockHttpClient):
        self.http = http

    def subscribe(self, user_id: str):
        return self.http.post(f"/subscriptions/{user_id}")

    def unsubscribe(self, user_id: str):
        return self.http.delete(f"/subscriptions/{user_id}")

    def get_incidences(self, user_id: str):
        return self.http.get(f"/incidences/{user_id}")

    def import_csv(self, path: str):
        return self.http.post("/import", json={"path": path})
