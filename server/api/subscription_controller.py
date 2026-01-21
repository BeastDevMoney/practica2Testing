from server.api.mock_http import Request, Response
from server.business_logic.subscription_service import SubscriptionService

class SubscriptionController:
    def __init__(self, sub_service: SubscriptionService):
        self.sub_service = sub_service

    def subscribe(self, req: Request, params):
        user_id = params["user_id"]
        self.sub_service.subscribe(user_id)
        return Response(200, {"ok": True, "subscribed": user_id})

    def unsubscribe(self, req: Request, params):
        user_id = params["user_id"]
        self.sub_service.unsubscribe(user_id)
        return Response(200, {"ok": True, "unsubscribed": user_id})
