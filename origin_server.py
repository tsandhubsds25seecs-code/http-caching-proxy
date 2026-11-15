"""
Simple origin server for testing the proxy.
"""

"""
Test origin server with controllable ETag / Last-Modified / Cache-Control.
"""
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

VERSION = {"n": 1}


class OriginHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            body = b"Hello from origin!\n"
        elif self.path == "/data.json":
            body = f'{{"version": {VERSION["n"]}, "data": "test"}}\n'.encode()
        elif self.path == "/change":
            VERSION["n"] += 1
            body = f'Version changed to {VERSION["n"]}\n'.encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        else:
            body = b"Not Found\n"
            self.send_response(404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        etag = f'"v{VERSION["n"]}"'
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=10")
        self.send_header("ETag", etag)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[ORIGIN] {self.address_string()} - {fmt % args}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()
    server = HTTPServer(("0.0.0.0", args.port), OriginHandler)
    print(f"[ORIGIN] Listening on port {args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
