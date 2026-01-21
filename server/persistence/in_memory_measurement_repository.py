from typing import List
from server.domain.measurement import Measurement

class InMemoryMeasurementRepository:
    def __init__(self):
        self._measurements: List[Measurement] = []

    def saveAll(self, ms: List[Measurement]) -> None:
        self._measurements.extend(ms)
        self._measurements.sort(key=lambda m: m.time)

    def findAll(self) -> List[Measurement]:
        return list(self._measurements)
