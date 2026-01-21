from typing import Dict, List
from server.publish_subscribe.subscriber import Subscriber
from server.domain.incidence import Incidence

class Publisher:
    def __init__(self):
        self._subs: Dict[str, Subscriber] = {}

    def subscribe(self, user_id: str) -> None:
        self._subs.setdefault(user_id, Subscriber(user_id))

    def unsubscribe(self, user_id: str) -> None:
        self._subs.pop(user_id, None)

    def notifySubscribers(self, incidences: List[Incidence]) -> None:
        for sub in self._subs.values():
            sub.updateIncidences(incidences)

    def pull(self, user_id: str) -> List[Incidence]:
        sub = self._subs.get(user_id)
        return [] if sub is None else sub.pull()

