from server.api.mock_http import Request, Response
from server.business_logic.measurement_service import MeasurementService
from server.business_logic.incidence_service import IncidenceService
from server.business_logic.subscription_service import SubscriptionService

class MeasurementController:
    def __init__(self,
                 m_service: MeasurementService,
                 i_service: IncidenceService,
                 s_service: SubscriptionService):
        self.m_service = m_service
        self.i_service = i_service
        self.s_service = s_service

    def import_csv(self, req: Request, params):
        path = (req.json or {}).get("path")
        if not path:
            return Response(400, {"error": "missing json.path"})

        ms = self.m_service.processCSV(path)
        incidences = self.i_service.computeIncidences()

        self.s_service.notifySubs(incidences)

        return Response(200, {
            "ok": True,
            "measurements": len(ms),
            "incidences": len(incidences)
        })
