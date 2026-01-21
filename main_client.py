from main_server import build_server
from server.api.mock_http import MockHttpClient
from client.service.client_api_service import ClientApiService
from client.app.app_controller import AppController
from client.ui.main_window import MainWindow

def main():
    server_app = build_server()
    http = MockHttpClient(server_app)

    api = ClientApiService(http)
    controller = AppController(api, user_id="alice")
    app = MainWindow(controller, csv_path="Dataset-CV.csv")
    app.mainloop()

if __name__ == "__main__":
    main()
