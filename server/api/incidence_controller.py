from server.api.mock_http import Request, Response
from server.publish_subscribe.publisher import Publisher

class IncidenceController:
    def __init__(self, publisher: Publisher):
        self.publisher = publisher

    def get_incidences(self, req: Request, params):
        user_id = params["user_id"]
        incidences = self.publisher.pull(user_id)
        return Response(200, {"user": user_id, "incidences": [i.to_dict() for i in incidences]})
