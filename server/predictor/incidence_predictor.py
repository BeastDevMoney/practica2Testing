from __future__ import annotations
from typing import Optional

from collections import defaultdict
from typing import List, Tuple
from uuid import uuid4
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from server.domain.measurement import Measurement
from server.domain.incidence import Incidence, IncidenceType
from server.predictor.scheduler import Scheduler


class Incidence_Predictor:
    def __init__(self, scheduler: Scheduler, train_ratio: float = 0.8, target_field: str = "vr1_a"):
        self.scheduler = scheduler
        self.train_ratio = train_ratio
        self.target_field = target_field

        self._pipeline = None

    def analyzeMeasurements(self, ms: List[Measurement]) -> List[Incidence]:
        ms = sorted(ms, key=lambda m: m.time)
        absences = self.scheduler.checkAbsences(ms, threshold_minutes=2)
        fj_jumps = self.scheduler.checkFrequencyJumps(ms, field=self.target_field, threshold_pct=50.0)
        return sorted(absences + fj_jumps, key=lambda i: i.start)

    def predict_voltage(self, ms: List[Measurement], target_field: Optional[str] = None) -> Tuple[list, "np.ndarray", "np.ndarray"]:
        
        from lightgbm import LGBMRegressor
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline

        if target_field is None:
            target_field = self.target_field

        ms = sorted(ms, key=lambda m: m.time)
        X, y, times = self._build_Xy_voltage(ms, target_field)

        n = len(y)
        split = int(n * self.train_ratio)
        if split < 5 or split >= n:
            print("No hay suficientes datos para entrenar/testear.")
            return [], np.array([]), np.array([])

        X_train, y_train = X[:split], y[:split]
        X_test, y_test = X[split:], y[split:]
        times_test = times[split:]

        self._pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("reg", LGBMRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                num_leaves=31,
                random_state=42,
                n_jobs=-1,
                verbose=-1,
            ))
        ])
        self._pipeline.fit(X_train, y_train)
        y_pred: "np.ndarray" = np.asarray(self._pipeline.predict(X_test), dtype=float)

        return times_test, y_test, y_pred

    def _build_Xy_voltage(self, ms: List[Measurement], target_field: str) -> Tuple["np.ndarray", "np.ndarray", list]:
        
        import math
        other_fields = [f for f in ["vr1_a", "vr2_a", "vr1_b", "vr2_b"] if f != target_field]

        def fval(m: Measurement, name: str) -> float:
            v = getattr(m, name, None)
            return np.nan if v is None else float(v)

        X_list, y_list, times = [], [], []

        for i in range(2, len(ms)):
            cur = ms[i]
            prev1 = ms[i - 1]
            prev2 = ms[i - 2]

            target_val = fval(cur, target_field)
            if np.isnan(target_val):
                continue

            hour_sin = math.sin(2 * math.pi * cur.time.hour / 24)
            hour_cos = math.cos(2 * math.pi * cur.time.hour / 24)
            dow = float(cur.time.weekday())

            status = np.nan if cur.status is None else float(cur.status)

            others_t = [fval(cur, f) for f in other_fields]

            lag1 = fval(prev1, target_field)
            lag2 = fval(prev2, target_field)
            delta1 = lag1 - lag2

            others_lag1 = [fval(prev1, f) for f in other_fields]

            x = ([status, hour_sin, hour_cos, dow]
                 + others_t
                 + [lag1, lag2, delta1]
                 + others_lag1)

            X_list.append(x)
            y_list.append(target_val)
            times.append(cur.time)

        return (np.array(X_list, dtype=float), np.array(y_list, dtype=float), times)

    def debug_evaluate_voltage(self, ms: List[Measurement], target_field: Optional[str] = None, window_minutes: int = 60) -> None:
        from sklearn.metrics import mean_absolute_error, mean_squared_error

        if target_field is None:
            target_field = self.target_field

        times, y_real, y_pred = self.predict_voltage(ms, target_field)
        if not len(times):
            return

        mae = mean_absolute_error(y_real, y_pred)
        rmse = np.sqrt(mean_squared_error(y_real, y_pred))

        print("=== VOLTAGE PREDICTION REPORT ===")
        print(f"Canal objetivo : {target_field}")
        print(f"Muestras test : {len(y_real)}")
        print(f"MAE : {mae:.2f} mV")
        print(f"RMSE : {rmse:.2f} mV")

        self._plot_voltage_prediction(times, y_real, y_pred, target_field, window_minutes)

    def _plot_voltage_prediction(self, times: list, y_real: "np.ndarray", y_pred: "np.ndarray", target_field: str, window_minutes: int = 60) -> None:
        t0 = times[0]
        xmin = np.array([(t - t0).total_seconds() / 60 for t in times])

        label_map = {
            "vr1_a": "Receptor 1 - canal A",
            "vr1_b": "Receptor 1 - canal B",
            "vr2_a": "Receptor 2 - canal A",
            "vr2_b": "Receptor 2 - canal B",
        }
        label = label_map.get(target_field, target_field)

        total_minutes = int(xmin[-1]) + 1

        for start in range(0, total_minutes, window_minutes):
            stop = start + window_minutes
            mask = (xmin >= start) & (xmin < stop)
            if not np.any(mask):
                continue

            plt.figure(figsize=(14, 4))
            plt.plot(xmin[mask], y_real[mask], label="Real", color="royalblue", linewidth=1.5)
            plt.plot(xmin[mask], y_pred[mask], label="Predicho (t+1)", color="darkorange", linewidth=1.5, linestyle="--")

            plt.fill_between(xmin[mask], y_real[mask], y_pred[mask], alpha=0.15, color="gray", label="Error")

            plt.title(f"{label} - {start} a {stop} min | "
                      f"MAE={np.mean(np.abs(y_real[mask]-y_pred[mask])):.1f} mV")
            plt.xlabel("Tiempo (min)")
            plt.ylabel("Voltaje (mV)")
            plt.legend()
            plt.ylim(bottom=0)
            plt.grid(True, alpha=0.4)
            plt.tight_layout()
            plt.show()

    def plot_voltages_raw(self, ms: List[Measurement], window_minutes: int = 60) -> None:
        ms = sorted(ms, key=lambda m: m.time)
        t0 = ms[0].time

        times_min = np.array([(m.time - t0).total_seconds() / 60 for m in ms])
        vr1_a = np.array([m.vr1_a if m.vr1_a is not None else np.nan for m in ms])
        vr1_b = np.array([m.vr1_b if m.vr1_b is not None else np.nan for m in ms])
        vr2_a = np.array([m.vr2_a if m.vr2_a is not None else np.nan for m in ms])
        vr2_b = np.array([m.vr2_b if m.vr2_b is not None else np.nan for m in ms])

        total_minutes = int(times_min[-1]) + 1

        for start in range(0, total_minutes, window_minutes):
            stop = start + window_minutes
            mask = (times_min >= start) & (times_min < stop)
            if not np.any(mask):
                continue

            fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

            axes[0].plot(times_min[mask], vr1_a[mask], label="R1 canal A", color="blue")
            axes[0].plot(times_min[mask], vr1_b[mask], label="R1 canal B", color="cyan")
            axes[0].set_title(f"Receptor 1 - {start} a {stop} min")
            axes[0].set_ylabel("Voltaje (mV)")
            axes[0].legend()
            axes[0].grid(True, alpha=0.4)

            axes[1].plot(times_min[mask], vr2_a[mask], label="R2 canal A", color="green")
            axes[1].plot(times_min[mask], vr2_b[mask], label="R2 canal B", color="lime")
            axes[1].set_title(f"Receptor 2 - {start} a {stop} min")
            axes[1].set_xlabel("Tiempo (min)")
            axes[1].set_ylabel("Voltaje (mV)")
            axes[1].legend()
            axes[1].grid(True, alpha=0.4)

            plt.tight_layout()
            plt.show()