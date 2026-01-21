from typing import Dict, List, Tuple
from server.domain.measurement import Measurement

class Train_Detector:
    def __init__(self):
        self.occupation_history: Dict[str, List[Tuple]] = {}

    def updateOcupation(self, ms: List[Measurement]) -> None:
        for m in ms:
            if m.status is None:
                continue
            track = m.track_id or "UNKNOWN"
            occupied = (m.status == 0)
            self.occupation_history.setdefault(track, []).append((m.time, occupied))

    def getOcupation(self, track_id: str = "7"):
        return list(self.occupation_history.get(track_id, []))
