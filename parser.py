class HTTPRequest:
    def _init_(self, method, target, version, headers, body):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers  # list of (name, value)
        self.body = body

    def get_header(self, name):
        for k, v in self.headers:
            if k.lower() == name.lower():
                return v
        return None

    def to_bytes(self):
        lines = [f"{self.method} {self.target} {self.version}"]
        for k, v in self.headers:
            lines.append(f"{k}: {v}")
        lines.append("")
        lines.append("")
        header_part = "\r\n".join(lines).encode()
        return header_part + (self.body or b"")


class HTTPResponse:
    def _init_(self, version, status, reason, headers, body):
        self.version = version
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    def get_header(self, name):
        for k, v in self.headers:
            if k.lower() == name.lower():
                return v
        return None

    def to_bytes(self):
        lines = [f"{self.version} {self.status} {self.reason}"]
        for k, v in self.headers:
            lines.append(f"{k}: {v}")
        lines.append("")
        lines.append("")
        header_part = "\r\n".join(lines).encode()
        return header_part + (self.body or b"")


def _read_headers(stream):
    lines = []
    headers = []
    while True:
        line = stream.readline()
        if not line:
            break
        lines.append(line)
        line_str = line.decode("latin-1").rstrip("\r\n")
        if line_str == "":
            break
        if ":" in line_str:
            k, v = line_str.split(":", 1)
            headers.append((k.strip(), v.strip()))
    return b"".join(lines), headers


def _read_body(stream, headers):
    header_map = {k.lower(): v for k, v in headers}

    # Chunked
    if "chunked" in header_map.get("transfer-encoding", "").lower():
        body = b""
        while True:
            size_line = stream.readline()
            if not size_line:
                break
            size_str = size_line.decode("latin-1").strip()
            if not size_str:
                continue
            chunk_size = int(size_str, 16)
            if chunk_size == 0:
                stream.readline()
                break
            chunk = stream.read(chunk_size)
            body += chunk
            stream.readline()
        return body

    # Content-Length
    length = header_map.get("content-length")
    if length:
        return stream.read(int(length))

    return b""


def parse_request(stream):
    request_line = stream.readline()
    if not request_line:
        return None
    line = request_line.decode("latin-1").rstrip("\r\n")
    parts = line.split(" ")
    if len(parts) != 3:
        raise ValueError(f"Invalid request line: {line}")
    method, target, version = parts

    _, headers = _read_headers(stream)
    body = _read_body(stream, headers)
    return HTTPRequest(method, target, version, headers, body)


def parse_response(stream):
    status_line = stream.readline()
    if not status_line:
        return None
    line = status_line.decode("latin-1").rstrip("\r\n")
    parts = line.split(" ", 2)
    if len(parts) < 2:
        raise ValueError(f"Invalid status line: {line}")
    version = parts[0]
    status = int(parts[1])
    reason = parts[2] if len(parts) > 2 else ""

    _, headers = _read_headers(stream)
    body = _read_body(stream, headers)
    return HTTPResponse(version, status, reason, headers, body)
