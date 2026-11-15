"""
Main proxy server.
Usage: python proxy.py --port 8080 --origin http://localhost:8000
"""
import argparse
import socket
import threading
import time
from urllib.parse import urlparse

from parser import parse_request, parse_response, HTTPRequest
from freshness import compute_freshness_lifetime, parse_date_header
from cache import CacheEntry, CacheStore
from revalidator import build_conditional_headers, is_304
from logger import ProxyLogger


class Proxy:
    def _init_(self, port, origin_host, origin_port, cache_store, logger):
        self.port = port
        self.origin_host = origin_host
        self.origin_port = origin_port
        self.cache = cache_store
        self.logger = logger

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", self.port))
        sock.listen(50)
        print(f"[PROXY] Listening on port {self.port}")
        print(f"[PROXY] Origin: {self.origin_host}:{self.origin_port}")
        while True:
            client_sock, addr = sock.accept()
            t = threading.Thread(target=self._handle_client,
                                 args=(client_sock, addr), daemon=True)
            t.start()

    def _handle_client(self, client_sock, addr):
        client_addr = f"{addr[0]}:{addr[1]}"
        start_time = time.time()
        try:
            stream = client_sock.makefile("rb")
            request = parse_request(stream)
            if request is None:
                return
            method = request.method
            uri = request.target

            if uri == "/stats":
                self._send_stats(client_sock)
                return

            cache_key = f"{method}:{uri}"
            cached = self.cache.get(cache_key)

            # HIT
            if cached and cached.is_fresh():
                response_bytes = self._build_cached_response(cached)
                client_sock.sendall(response_bytes)
                ms = (time.time() - start_time) * 1000
                self.logger.log(client_addr, method, uri, "HIT", ms, 0, cached.status)
                print(f"[HIT] {uri} ({ms:.1f}ms)")
                return

            # STALE → revalidate
            if cached:
                upstream_headers = list(request.headers) + build_conditional_headers(cached)
                req = HTTPRequest(method, uri, request.version, upstream_headers, b"")
                origin_resp = self._forward(req)
                if origin_resp is None:
                    self._send_error(client_sock, 504, "Gateway Timeout")
                    self.logger.log(client_addr, method, uri, "BYPASS", 0, 0, 504)
                    return

                if is_304(origin_resp):
                    cached.refresh_metadata(origin_resp.headers)
                    client_sock.sendall(self._build_cached_response(cached))
                    ms = (time.time() - start_time) * 1000
                    self.logger.log(client_addr, method, uri, "REVALIDATED-304", ms,
                                    len(origin_resp.body), 200)
                    print(f"[REVALIDATED-304] {uri} ({ms:.1f}ms)")
                else:
                    self._store_if_cacheable(cache_key, origin_resp)
                    client_sock.sendall(origin_resp.to_bytes())
                    ms = (time.time() - start_time) * 1000
                    self.logger.log(client_addr, method, uri, "REVALIDATED-200", ms,
                                    len(origin_resp.body), origin_resp.status)
                    print(f"[REVALIDATED-200] {uri} ({ms:.1f}ms)")
                return

            # MISS
            origin_resp = self._forward(request)
            if origin_resp is None:
                self._send_error(client_sock, 504, "Gateway Timeout")
                self.logger.log(client_addr, method, uri, "BYPASS", 0, 0, 504)
                return

            stored = self._store_if_cacheable(cache_key, origin_resp)
            client_sock.sendall(origin_resp.to_bytes())
            ms = (time.time() - start_time) * 1000
            status_label = "MISS" if stored else "BYPASS"
            self.logger.log(client_addr, method, uri, status_label, ms,
                            len(origin_resp.body), origin_resp.status)
            print(f"[{status_label}] {uri} ({ms:.1f}ms)")

        except Exception as e:
            print(f"[ERROR] {e}")
            try:
                self._send_error(client_sock, 500, "Internal Server Error")
            except Exception:
                pass
        finally:
            client_sock.close()

    def _forward(self, request):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect((self.origin_host, self.origin_port))
            s.sendall(request.to_bytes())
            stream = s.makefile("rb")
            response = parse_response(stream)
            s.close()
            return response
        except Exception as e:
            print(f"[ORIGIN ERROR] {e}")
            return None

    def _store_if_cacheable(self, key, response):
        if response.status != 200:
            return False
        lifetime = compute_freshness_lifetime(response.headers)
        if lifetime is None:
            return False
        header_map = {k.lower(): v for k, v in response.headers}
        date_val = parse_date_header(header_map.get("date", "")) or time.time()
        entry = CacheEntry(
            status=response.status,
            reason=response.reason,
            version=response.version,
            headers=response.headers,
            body=response.body,
            date_value=date_val,
            age_value=0,
            freshness_lifetime=lifetime,
            etag=header_map.get("etag"),
            last_modified=header_map.get("last-modified"),
        )
        self.cache.put(key, entry)
        return True

    def _build_cached_response(self, entry):
        from parser import HTTPResponse
        resp = HTTPResponse(entry.version, entry.status, entry.reason,
                            entry.headers, entry.body)
        return resp.to_bytes()

    def _send_error(self, sock, code, reason):
        body = f"{code} {reason}".encode()
        resp = (f"HTTP/1.1 {code} {reason}\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"Content-Type: text/plain\r\n"
                f"\r\n").encode() + body
        sock.sendall(resp)

    def _send_stats(self, sock):
        import json
        body = json.dumps(self.logger.summary(), indent=2).encode()
        resp = (f"HTTP/1.1 200 OK\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"Content-Type: application/json\r\n"
                f"\r\n").encode() + body
        sock.sendall(resp)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--origin", type=str, default="http://localhost:8000")
    args = p.parse_args()

    origin = urlparse(args.origin)
    host = origin.hostname or "localhost"
    port = origin.port or 80

    cache = CacheStore()
    logger = ProxyLogger("proxy.log")
    proxy = Proxy(args.port, host, port, cache, logger)
    proxy.start()


if _name_ == "_main_":
    main()