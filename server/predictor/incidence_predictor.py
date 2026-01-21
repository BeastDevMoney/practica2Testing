from __future__ import annotations
from typing import List, Tuple
from uuid import uuid4

from server.domain.measurement import Measurement
from server.domain.incidence import Incidence, IncidenceType
from server.predictor.scheduler import Scheduler

# Modelo de ML con scikit-learn usado para predecir las incidencias
class Incidence_Predictor:
    def __init__(self, scheduler: Scheduler, jump_threshold: float = 500.0, train_ratio: float = 0.8):
        self.scheduler = scheduler
        self.jump_threshold = jump_threshold
        self.train_ratio = train_ratio

        self._model = None
        self._pipeline = None

    def analyzeMeasurements(self, ms: List[Measurement]) -> List[Incidence]:
        ms = sorted(ms, key=lambda m: m.time)

        incidences: List[Incidence] = []

        incidences.extend(self.scheduler.checkAbsences(ms, threshold_minutes=2))

        if len(ms) >= 10:
            ml_incs = self._predict_frequency_jump_ml(ms)
            incidences.extend(ml_incs)

        return incidences

    def _predict_frequency_jump_ml(self, ms: List[Measurement]) -> List[Incidence]:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline

        X, y, windows = self._build_Xy(ms)

        n = len(y)
        split = int(n * self.train_ratio)
        if split <= 1 or split >= n:
            return []

        X_train, y_train = X[:split], y[:split]
        X_test = X[split:]
        windows_test = windows[split:]

        self._pipeline = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight="balanced_subsample"
            ))
        ])

        self._pipeline.fit(X_train, y_train)

        proba = self._pipeline.predict_proba(X_test)
        p1 = proba[:, 1]
        preds = (p1 >= 0.5).astype(int)

        out: List[Incidence] = []
        for pred, prob, (t0, t1) in zip(preds, p1, windows_test):
            if pred == 1:
                out.append(Incidence(
                    incidenceID=str(uuid4()),
                    tipoIncidencia=IncidenceType.FREQUENCY_JUMP,
                    start=t0,
                    end=t1,
                    details=f"ML predicted jump between {t0} and {t1} (p={prob:.3f})"
                ))
        return out

    def _build_Xy(self, ms: List[Measurement]) -> Tuple["np.ndarray", "np.ndarray", List[Tuple]]:
        import numpy as np

        fields = ["vr1_a", "vr2_a", "vr1_b", "vr2_b"]

        def fval(m: Measurement, name: str):
            v = getattr(m, name)
            return np.nan if v is None else float(v)

        X_list = []
        y_list = []
        windows = []

        for i in range(len(ms) - 1):
            cur = ms[i]
            nxt = ms[i + 1]
            prev = ms[i - 1] if i > 0 else None

            status = np.nan if cur.status is None else float(cur.status)

            vals = [fval(cur, f) for f in fields]
            miss = [1.0 if (getattr(cur, f) is None) else 0.0 for f in fields]

            if prev is None:
                deltas = [np.nan] * len(fields)
            else:
                deltas = []
                for f in fields:
                    vc = fval(cur, f)
                    vp = fval(prev, f)
                    deltas.append(vc - vp)

            x = [status] + vals + deltas + miss
            X_list.append(x)

            jump = 0
            for f in fields:
                v1 = getattr(cur, f)
                v2 = getattr(nxt, f)
                if v1 is None or v2 is None:
                    continue
                if abs(float(v2) - float(v1)) >= self.jump_threshold:
                    jump = 1
                    break

            y_list.append(jump)
            windows.append((cur.time, nxt.time))

        return np.array(X_list, dtype=float), np.array(y_list, dtype=int), windows

    def debug_evaluate_jump(self, ms):
        from sklearn.metrics import classification_report, confusion_matrix
        import numpy as np

        ms = sorted(ms, key=lambda m: m.time)
        X, y, windows = self._build_Xy(ms)

        n = len(y)
        split = int(n * self.train_ratio)
        X_train, y_train = X[:split], y[:split]
        X_test, y_test = X[split:], y[split:]
        windows_test = windows[split:]

        from sklearn.ensemble import RandomForestClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline

        pipe = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight="balanced_subsample"
            ))
        ])
        pipe.fit(X_train, y_train)

        proba = pipe.predict_proba(X_test)[:, 1]
        preds = (proba >= 0.5).astype(int)

        print("=== JUMP DEBUG REPORT ===")
        print("Total samples:", n)
        print("Train:", len(y_train), "Test:", len(y_test))
        print("Real jump rate (test):", float(np.mean(y_test)))
        print("Pred jump rate (test):", float(np.mean(preds)))
        print("Confusion matrix:\n", confusion_matrix(y_test, preds))
        print(classification_report(y_test, preds, digits=3))

        top_idx = np.argsort(-proba)[:10]
        print("\nTop 10 predicted probabilities (test):")
        for k in top_idx:
            t0, t1 = windows_test[k]
            print(f"p={proba[k]:.3f} pred={preds[k]} real={y_test[k]} window={t0} -> {t1}")

        self._pipeline = pipe


