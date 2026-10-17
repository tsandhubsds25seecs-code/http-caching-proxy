"""
Simple origin server for testing the proxy.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler


class OriginHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Cache-Control", "max-age=60")
        self.send_header("ETag", '"v1"')
        self.end_headers()
        self.wfile.write(b"Hello from origin")


def main():
    server = HTTPServer(("0.0.0.0", 8000), OriginHandler)
    print("Origin server on port 8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
