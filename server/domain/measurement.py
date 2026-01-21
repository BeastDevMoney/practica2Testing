from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Measurement:
    time: datetime
    status: Optional[int]
    vr1_a: Optional[float]
    vr2_a: Optional[float]
    vr1_b: Optional[float]
    vr2_b: Optional[float]
    track_id: Optional[str] = None
    def __str__(self) -> str:
        return (f"[{self.time:%Y-%m-%d %H:%M}] status={self.status} "
                f"vr1_a={self.vr1_a} vr2_a={self.vr2_a} "
                f"vr1_b={self.vr1_b} vr2_b={self.vr2_b} track={self.track_id}")
