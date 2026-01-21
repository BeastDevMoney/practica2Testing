from dataclasses import dataclass
from datetime import datetime

@dataclass
class IncidenceDTO:
    incidenceID: str
    tipoIncidencia: str
    start: datetime
    end: datetime
    details: str
