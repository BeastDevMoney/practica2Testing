from typing import List
from server.publish_subscribe.publisher import Publisher
from server.domain.incidence import Incidence

class SubscriptionService:
    def __init__(self, publisher: Publisher):
        self.publisher = publisher

    def subscribe(self, user_id: str) -> None:
        self.publisher.subscribe(user_id)

    def unsubscribe(self, user_id: str) -> None:
        self.publisher.unsubscribe(user_id)

    def notifySubs(self, incidences: List[Incidence]) -> None:
        self.publisher.notifySubscribers(incidences)
