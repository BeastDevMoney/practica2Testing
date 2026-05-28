from server.api.app_factory import build_server_api
from server.api.measurement_controller import MeasurementController
from server.api.subscription_controller import SubscriptionController
from server.api.incidence_controller import IncidenceController
from server.api.mock_http import MockHttpClient
from server.integration.csv_reader import CSVReader
from server.persistence.in_memory_measurement_repository import InMemoryMeasurementRepository
from server.persistence.in_memory_incidence_repository import InMemoryIncidenceRepository
from server.business_logic.train_detector import Train_Detector
from server.business_logic.measurement_service import MeasurementService
from server.business_logic.incidence_service import IncidenceService
from server.predictor.scheduler import Scheduler
from server.predictor.incidence_predictor import Incidence_Predictor
from server.publish_subscribe.publisher import Publisher
from server.business_logic.subscription_service import SubscriptionService
from client.service.client_api_service import ClientApiService
from client.app.app_controller import AppController
from client.ui.main_window import MainWindow

CSV_PATH = "Dataset-CV.csv"

if __name__ == "__main__":
    reader = CSVReader()
    m_repo = InMemoryMeasurementRepository()
    i_repo = InMemoryIncidenceRepository()
    detector = Train_Detector()
    m_service = MeasurementService(reader, m_repo, detector)
    scheduler = Scheduler()
    predictor = Incidence_Predictor(scheduler, target_field="vr1_a")
    i_service = IncidenceService(m_repo, i_repo, predictor)
    publisher = Publisher()
    sub_service = SubscriptionService(publisher)
    m_controller = MeasurementController(m_service, i_service, sub_service)
    s_controller = SubscriptionController(sub_service)
    i_controller = IncidenceController(publisher)
    server_app = build_server_api(m_controller, i_controller, s_controller)

    http = MockHttpClient(server_app)
    api = ClientApiService(http)
    controller = AppController(api, user_id="alice")

    app = MainWindow(controller, CSV_PATH)
    app.mainloop()