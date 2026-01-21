from datetime import datetime
from client.domain.incidence_dto import IncidenceDTO
from client.service.client_api_service import ClientApiService

class AppController:
    def __init__(self, api: ClientApiService, user_id: str):
        self.api = api
        self.user_id = user_id
        self.received_incidences: list[IncidenceDTO] = []

    def subscribe(self):
        self.api.subscribe(self.user_id)

    def unsubscribe(self):
        self.api.unsubscribe(self.user_id)

    def refresh(self) -> list[IncidenceDTO]:
        r = self.api.get_incidences(self.user_id)
        incs = r.json.get("incidences", [])
        self.received_incidences = [
            IncidenceDTO(
                incidenceID=i["incidenceID"],
                tipoIncidencia=i["tipoIncidencia"],
                start=datetime.fromisoformat(i["start"]),
                end=datetime.fromisoformat(i["end"]),
                details=i["details"],
            )
            for i in incs
        ]
        return self.received_incidences

    def bootstrap(self, csv_path: str):
        self.subscribe()
        r = self.api.import_csv(csv_path)
        return r
