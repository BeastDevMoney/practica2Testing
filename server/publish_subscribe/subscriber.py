from typing import List
from server.domain.incidence import Incidence

class Subscriber:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._inbox: List[Incidence] = []

    def updateIncidences(self, incidences: List[Incidence]) -> None:
        self._inbox.extend(incidences)

    def pull(self) -> List[Incidence]:
        out = list(self._inbox)
        self._inbox.clear()
        return out
