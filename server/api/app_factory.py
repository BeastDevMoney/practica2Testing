from server.api.mock_http import MockHttpServer
from server.api.measurement_controller import MeasurementController
from server.api.incidence_controller import IncidenceController
from server.api.subscription_controller import SubscriptionController

def build_server_api(m_controller: MeasurementController,
                     i_controller: IncidenceController,
                     s_controller: SubscriptionController) -> MockHttpServer:
    app = MockHttpServer()
    app.add_route("POST", "/import", m_controller.import_csv)
    app.add_route("POST", "/subscriptions/{user_id}", s_controller.subscribe)
    app.add_route("DELETE", "/subscriptions/{user_id}", s_controller.unsubscribe)
    app.add_route("GET", "/incidences/{user_id}", i_controller.get_incidences)
    return app
