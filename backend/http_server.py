from http.server import ThreadingHTTPServer

from .request_handler import ChatRequestHandler


class ChatHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address, application):
        self.application = application
        super().__init__(server_address, ChatRequestHandler)
