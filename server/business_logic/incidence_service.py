from server.persistence.in_memory_measurement_repository import InMemoryMeasurementRepository
from server.persistence.in_memory_incidence_repository import InMemoryIncidenceRepository
from server.predictor.incidence_predictor import Incidence_Predictor

class IncidenceService:
    def __init__(self, m_repo: InMemoryMeasurementRepository, i_repo: InMemoryIncidenceRepository, predictor: Incidence_Predictor):
        self.m_repo = m_repo
        self.i_repo = i_repo
        self.predictor = predictor

    def computeIncidences(self, mode=0):
        ms = self.m_repo.findAll()

        if mode == 1:
            print("DEBUG MODE")
            self.predictor.debug_evaluate_jump(ms)

        incidences = self.predictor.analyzeMeasurements(ms)
        self.i_repo.saveAll(incidences)
        return incidences
