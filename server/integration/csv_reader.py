import csv
from datetime import datetime
from statistics import mean
from typing import List, Optional

from server.domain.measurement import Measurement

class CSVReader:

    def readCSV(self, path: str) -> List[Measurement]:
        out: List[Measurement] = []

        current_time: Optional[datetime] = None
        current_track_id: Optional[str] = None

        status_vals: List[int] = []
        vr1_a_vals: List[float] = []
        vr2_a_vals: List[float] = []
        vr1_b_vals: List[float] = []
        vr2_b_vals: List[float] = []

        def flush_minute() -> None:
            nonlocal status_vals, vr1_a_vals, vr2_a_vals, vr1_b_vals, vr2_b_vals
            nonlocal current_time, current_track_id, out

            if current_time is None:
                return

            status: Optional[int] = min(status_vals) if status_vals else None

            def avg(xs: List[float]) -> Optional[float]:
                return mean(xs) if xs else None

            m = Measurement(
                time=current_time,
                status=status,
                vr1_a=avg(vr1_a_vals),
                vr2_a=avg(vr2_a_vals),
                vr1_b=avg(vr1_b_vals),
                vr2_b=avg(vr2_b_vals),
                track_id=current_track_id,
            )
            out.append(m)

            status_vals = []
            vr1_a_vals = []
            vr2_a_vals = []
            vr1_b_vals = []
            vr2_b_vals = []

        with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")

            for row in reader:
                medida = row["medida"].strip()
                tiempo_raw = row["tiempo"].strip()
                canal = row["canal"].strip()
                track_id = row["id"].strip()
                valor_raw = row["valor"].strip().replace(",", ".")

                t = datetime.strptime(tiempo_raw, "%d/%m/%Y %H:%M")
                v = float(valor_raw)

                if current_time is None:
                    current_time = t
                    current_track_id = track_id
                elif t != current_time:
                    flush_minute()
                    current_time = t
                    current_track_id = track_id

                if medida == "status":
                    status_vals.append(int(v))
                elif medida == "voltageReceiver1":
                    if canal == "a":
                        vr1_a_vals.append(v)
                    elif canal == "b":
                        vr1_b_vals.append(v)
                elif medida == "voltageReceiver2":
                    if canal == "a":
                        vr2_a_vals.append(v)
                    elif canal == "b":
                        vr2_b_vals.append(v)

        flush_minute()

        return out
