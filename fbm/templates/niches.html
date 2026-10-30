def wait_for_callback(timeout=300, path="/callback"):
    """Blocking loopback listener with a friendly success page and error surfacing."""
    result = {}
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            result.update(q)
            ok = "code" in q or "access_token" in q
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
            self.wfile.write((SUCCESS if ok else FAIL).encode())
        def log_message(self,*a): pass
    srv = http.server.HTTPServer(("127.0.0.1", 8765), H)
    srv.timeout = timeout
    while not result:
        srv.handle_request()
    return result

SUCCESS = "<h3>Connected — return to the app.</h3><script>setTimeout(()=>window.close(),1200)</script>"
FAIL    = "<h3>Something went wrong — check the app for details.</h3>"
