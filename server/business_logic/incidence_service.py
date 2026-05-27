import os
import tempfile
import numpy as np
from server.persistence.in_memory_measurement_repository import InMemoryMeasurementRepository
from server.persistence.in_memory_incidence_repository import InMemoryIncidenceRepository
from server.predictor.incidence_predictor import Incidence_Predictor

PREDICTION_CACHE = os.path.join(tempfile.gettempdir(), "voltage_prediction_cache")


class IncidenceService:
    def __init__(self, m_repo: InMemoryMeasurementRepository,
                 i_repo: InMemoryIncidenceRepository,
                 predictor: Incidence_Predictor):
        self.m_repo = m_repo
        self.i_repo = i_repo
        self.predictor = predictor

    def computeIncidences(self, mode=0):
        ms = self.m_repo.findAll()
        incidences = self.predictor.analyzeMeasurements(ms)
        self.i_repo.saveAll(incidences)
        return incidences

    def trainPredictor(self, target_field: str = "vr1_a") -> None:
        print(f"[IncidenceService] Entrenando predictor para canal {target_field}...")
        ms = self.m_repo.findAll()

        self.predictor.target_field = target_field

        times, y_real, y_pred = self.predictor.predict_voltage(ms, target_field)
        if not len(times):
            print("[IncidenceService] No se pudo entrenar el modelo.")
            return

        times_epoch = np.array([t.timestamp() for t in times], dtype=np.float64)

        cache_file = f"{PREDICTION_CACHE}_{target_field}.npz"
        np.savez(
            cache_file,
            times_epoch=times_epoch,
            y_real=y_real,
            y_pred=y_pred,
            target_field=np.array([target_field]),
        )
        print(f"[IncidenceService] Entrenamiento completado. Cache guardado en {cache_file}")