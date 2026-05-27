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

    def checkFrequencyJumps(self, ms: List[Measurement], field: str = "vr1_b", threshold_pct: float = 50.0, max_gap_minutes: int = 5) -> List[Incidence]:
        incidences: List[Incidence] = []
        if len(ms) < 2:
            return incidences

        max_gap = timedelta(minutes=max_gap_minutes)

        for prev, curr in zip(ms, ms[1:]):
            if (curr.time - prev.time) > max_gap:
                continue

            vp = getattr(prev, field)
            vc = getattr(curr, field)

            if vp is None or vc is None or vp == 0:
                continue

            delta_pct = abs(vc - vp) / abs(vp) * 100.0

            if delta_pct >= threshold_pct:
                incidences.append(Incidence(
                    incidenceID=str(uuid4()),
                    tipoIncidencia=IncidenceType.FREQUENCY_JUMP,
                    start=curr.time,
                    end=curr.time + timedelta(minutes=1),
                    details=f"{field}: {vp:.0f} -> {vc:.0f} mV ({delta_pct:.1f}%)"
                ))

        return incidences