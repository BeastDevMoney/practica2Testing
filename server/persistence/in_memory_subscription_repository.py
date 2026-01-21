from typing import List, Set
from server.domain.subscription import Subscription

class InMemorySubscriptionRepository:
    def __init__(self):
        self._subs: Set[str] = set()

    def save(self, s: Subscription) -> None:
        self._subs.add(s.user_id)

    def delete(self, user_id: str) -> None:
        self._subs.discard(user_id)

    def findAll(self) -> List[Subscription]:
        return [Subscription(uid) for uid in sorted(self._subs)]
