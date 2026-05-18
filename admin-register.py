import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

GAME_SERVER = "http://127.0.0.1:9090"

class AdminRegisterHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        if self.path != "/admin/register/account":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        email = body.get("email", "")
        username = body.get("username", "")
        password = body.get("password", "")
        dashboard_token = body.get("token", "")

        if not email or not username or not password:
            self._respond(400, "MISSING_FIELDS", "Email, username, and password required")
            return

        # Verify admin token
        auth_headers = {
            "Content-Type": "application/json",
            "Authorization": dashboard_token,
        }
        req = urllib.request.Request(
            f"{GAME_SERVER}/dashboard/config",
            headers=auth_headers,
            method="GET",
        )
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            if resp.getcode() != 200:
                self._respond(401, "UNAUTHORIZED", "Invalid admin token")
                return
        except (urllib.error.HTTPError, urllib.error.URLError):
            self._respond(401, "UNAUTHORIZED", "Invalid admin token")
            return

        # Forward registration (bypasses IP rate limiter via localhost)
        reg_data = json.dumps({
            "email": email,
            "username": username,
            "password": password,
            "captcha": "admin-bypass",
            "otp": "admin-bypass",
        }).encode()
        reg_headers = {"Content-Type": "application/json"}
        reg_req = urllib.request.Request(
            f"{GAME_SERVER}/login/register/account",
            data=reg_data,
            headers=reg_headers,
            method="POST",
        )
        try:
            resp = urllib.request.urlopen(reg_req, timeout=10)
            result = json.loads(resp.read())
            self._respond(result.get("code", 500), result.get("message", "UNKNOWN"))
        except urllib.error.HTTPError as e:
            err_body = e.read()
            try:
                result = json.loads(err_body)
                self._respond(result.get("code", 500), result.get("message", "PROXY_ERROR"))
            except json.JSONDecodeError:
                self._respond(500, "PROXY_ERROR")

    def _respond(self, code, message, detail=None):
        self.send_response(200 if code == 200 else code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        resp = {"code": code, "message": message}
        if detail:
            resp["detail"] = detail
        self.wfile.write(json.dumps(resp).encode())

    def log_message(self, format, *args):
        print(f"[admin-register] {args[0]} {args[1]} {args[2]}")

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9191), AdminRegisterHandler)
    print("Admin register proxy listening on 127.0.0.1:9191")
    server.serve_forever()
