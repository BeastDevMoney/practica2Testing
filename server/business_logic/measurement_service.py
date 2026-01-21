from server.integration.csv_reader import CSVReader
from server.persistence.in_memory_measurement_repository import InMemoryMeasurementRepository
from server.business_logic.train_detector import Train_Detector

class MeasurementService:
    def __init__(self, reader: CSVReader, repo: InMemoryMeasurementRepository, detector: Train_Detector):
        self.reader = reader
        self.repo = repo
        self.detector = detector

    def processCSV(self, path: str):
        ms = self.reader.readCSV(path)
        self.repo.saveAll(ms)
        self.detector.updateOcupation(ms)
        return ms
