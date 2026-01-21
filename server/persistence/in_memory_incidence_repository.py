from typing import List
from server.domain.incidence import Incidence

class InMemoryIncidenceRepository:
    def __init__(self):
        self._incidences: List[Incidence] = []

    def saveAll(self, incidences: List[Incidence]) -> None:
        self._incidences.extend(incidences)
        self._incidences.sort(key=lambda i: i.start)

    def findAll(self) -> List[Incidence]:
        return list(self._incidences)
