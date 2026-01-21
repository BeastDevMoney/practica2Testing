from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class IncidenceType(Enum):
    ABSENCE = 1
    FREQUENCY_JUMP = 2

@dataclass
class Incidence:
    incidenceID: str
    tipoIncidencia: IncidenceType
    start: datetime
    end: datetime
    details: str

    def __str__(self) -> str:
        return (f"[{self.tipoIncidencia.name}] {self.start:%Y-%m-%d %H:%M} -> {self.end:%Y-%m-%d %H:%M} "
                f"id={self.incidenceID[:8]} details={self.details}")

    def to_dict(self) -> dict:
        return {
            "incidenceID": self.incidenceID,
            "tipoIncidencia": self.tipoIncidencia.name,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "details": self.details,
        }


