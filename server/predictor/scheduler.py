from datetime import timedelta
from typing import List
from uuid import uuid4
from server.domain.measurement import Measurement
from server.domain.incidence import Incidence, IncidenceType

class Scheduler:
    def checkAbsences(self, ms: List[Measurement], threshold_minutes: int = 2) -> List[Incidence]:
        incidences: List[Incidence] = []
        if len(ms) < 2:
            return incidences

        thr = timedelta(minutes=threshold_minutes)
        for prev, curr in zip(ms, ms[1:]):
            gap = curr.time - prev.time
            if gap > thr:
                incidences.append(Incidence(
                    incidenceID=str(uuid4()),
                    tipoIncidencia=IncidenceType.ABSENCE,
                    start=prev.time,
                    end=curr.time,
                    details=f"Gap without data: {gap}"
                ))
        return incidences
