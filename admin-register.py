import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

GAME_SERVER = "http://127.0.0.1:9090"

REGISTER_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Create Account</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f1117; color: #e1e4e8; display:flex; justify-content:center; align-items:center; min-height:100vh; }
.card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:28px; width:400px; }
h1 { font-size:22px; text-align:center; margin-bottom:20px; color:#f0f2f5; }
.form-group { margin-bottom:14px; }
.form-group label { display:block; font-size:12px; color:#8b949e; margin-bottom:4px; }
.form-group input { width:100%; padding:10px; background:#0d1117; border:1px solid #30363d; border-radius:6px; color:#e1e4e8; font-size:14px; }
.form-group input:focus { outline:none; border-color:#58a6ff; }
.btn { width:100%; padding:10px; border:none; border-radius:6px; font-size:14px; cursor:pointer; font-weight:600; background:#238636; color:#fff; }
.btn:hover { background:#2ea043; }
.btn:disabled { opacity:0.6; cursor:not-allowed; }
.error { color:#f85149; font-size:12px; margin-top:8px; display:none; }
.success { color:#3fb950; font-size:12px; margin-top:8px; display:none; }
.info-text { font-size:11px; color:#8b949e; margin-top:4px; }
.step { font-size:12px; color:#8b949e; margin-top:10px; }
.back-link { display:block; text-align:center; margin-top:12px; font-size:12px; }
.back-link a { color:#58a6ff; text-decoration:none; }
</style>
</head>
<body>
<div class="card">
  <h1>Create Game Account</h1>
  <div class="form-group"><label>Username</label><input type="text" id="username" placeholder="PlayerName" autocomplete="off"></div>
  <div class="form-group"><label>Password</label><input type="password" id="password" placeholder="Password"></div>
  <div class="form-group"><label>Email</label><input type="text" id="email" placeholder="player@example.com"></div>
  <button class="btn" id="create-btn" onclick="doCreate()">Create Account</button>
  <div class="error" id="error"></div>
  <div class="success" id="success"></div>
  <div class="step" id="step"></div>
  <div class="back-link"><a href="http://{}:{}/dashboard.html" target="_blank">Back to Dashboard</a></div>
</div>
<script>
const stepEl = document.getElementById('step');
const errEl = document.getElementById('error');
const succEl = document.getElementById('success');

function htmlEncode(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function step(msg) { stepEl.textContent = msg; }
function setError(msg) { errEl.textContent = msg; errEl.style.display = 'block'; succEl.style.display = 'none'; }
function setSuccess(msg) { succEl.innerHTML = msg; succEl.style.display = 'block'; errEl.style.display = 'none'; }

async function doCreate() {
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  const email = document.getElementById('email').value.trim();
  const btn = document.getElementById('create-btn');

  setError(''); setSuccess(''); step('');
  if (!username || !password || !email) { setError('All fields required.'); return; }
  btn.disabled = true;

  try {
    // 1. Register
    step('Registering account...');
    let r = await fetch('/admin/create', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username, password, email})
    });
    let d = await r.json();
    if (d.code !== 200) { setError(d.message || 'Registration failed'); btn.disabled = false; return; }

    setSuccess('Account <b>' + htmlEncode(username) + '</b> created! Password: ' + htmlEncode(password) +
      '<br><span class="info-text">Login at /login/login/account</span>');
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('email').value = '';
  } catch (e) {
    setError('Error: ' + e.message);
  }
  btn.disabled = false;
  step('');
}
</script>
</body>
</html>'''

FIX_FIELDS_SCRIPT = '''
  var user = db.game_users.findOne({username: "%s"});
  if (!user) { print("USER_NOT_FOUND"); quit(); }

  var userIdStr = user._id.toString();
  var oldUserId = NumberInt(user.userId.valueOf());
  var setFields = {};

  if (!user.game_tasks || !user.game_tasks.currentDaily) {
    setFields["game_tasks.currentDaily"] = [];
  }
  if (!user.game_tasks || !user.game_tasks.claimedDailyAwards) {
    setFields["game_tasks.claimedDailyAwards"] = [];
  }
  if (!user.game_ships || !user.game_ships.repair) {
    setFields["game_ships.repair"] = [];
  }
  if (!user.game_bionic_chips || !user.game_bionic_chips.phases) {
    setFields["game_bionic_chips.phases"] = [1,0,0,0,0];
  }
  if (!user.game_rewards || !user.game_rewards.until) {
    setFields["game_rewards.until"] = new Date();
  }
  if (!user.game_stats || !user.game_stats.iglStats) {
    setFields["game_stats.iglStats"] = {claimed: false, entries: 0, fleetIds: [], rank: 0};
  }
  if (!user.game_user_emails) {
    setFields["game_user_emails"] = {userEmails: []};
  }

  var dupUser = db.game_users.findOne({userId: user.userId, _id: {$ne: user._id}});
  if (dupUser) {
    var maxUid = db.game_users.aggregate([{$group: {_id: null, max: {$max: "$userId"}}}]).toArray();
    var maxPlanetUid = db.game_planets.aggregate([{$group: {_id: null, max: {$max: "$userId"}}}]).toArray();
    var maxAll = Math.max(
      maxUid.length > 0 ? NumberInt(maxUid[0].max) : 0,
      maxPlanetUid.length > 0 ? NumberInt(maxPlanetUid[0].max) : 0
    );
    var newUid = NumberInt(maxAll + 1);
    setFields["userId"] = newUid;
    db.game_planets.updateOne(
      {userObjectId: userIdStr, type: "USER_PLANET"},
      {$set: {userId: newUid}}
    );
    print("USERID_FIX:" + oldUserId + "->" + newUid);
  }

  if (Object.keys(setFields).length > 0) {
    db.game_users.updateOne({_id: user._id}, {$set: setFields});
    print("FIXED:" + Object.keys(setFields).join(","));
  } else {
    print("NO_FIX_NEEDED");
  }
'''

class AdminRegisterHandler(BaseHTTPRequestHandler):
    server_ip = "127.0.0.1"
    server_port = "9090"

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/register", "/register.html"):
            html = REGISTER_HTML.replace("{}", self.server_ip).replace("{}", self.server_port)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
        elif self.path == "/admin/health":
            self._respond(200, "UP")
        elif self.path == "/admin/list":
            self._handle_list()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/admin/create":
            self._handle_create()
        elif self.path == "/admin/finalize":
            self._handle_finalize()
        else:
            self.send_error(404)

    def _handle_create(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        username = body.get("username", "")
        password = body.get("password", "")
        email = body.get("email", "")

        if not username or not password or not email:
            self._respond(400, "All fields required")
            return

        try:
            # Step 1: Register
            reg_data = json.dumps({"email": email, "username": username, "password": password, "captcha": "admin-bypass", "otp": "admin-bypass"}).encode()
            reg_req = urllib.request.Request(f"{GAME_SERVER}/login/register/account", data=reg_data, headers={"Content-Type": "application/json"}, method="POST")
            reg_resp = urllib.request.urlopen(reg_req, timeout=10)
            reg_result = json.loads(reg_resp.read())
            if reg_result.get("code") != 200:
                self._respond(500, "Registration failed: " + reg_result.get("message", "UNKNOWN"))
                return

            # Step 2: Login
            login_data = json.dumps({"username": username, "password": password}).encode()
            login_req = urllib.request.Request(f"{GAME_SERVER}/login/login/account", data=login_data, headers={"Content-Type": "application/json"}, method="POST")
            login_resp = urllib.request.urlopen(login_req, timeout=10)
            login_result = json.loads(login_resp.read())
            if login_result.get("code") != 200:
                self._respond(500, "Login failed after registration")
                return
            token = login_result.get("data", {}).get("token", "")
            if not token:
                self._respond(500, "No token received after login")
                return

            # Step 3: Create character
            char_data = json.dumps({"username": username, "ground": 1}).encode()
            char_req = urllib.request.Request(f"{GAME_SERVER}/account/create/user", data=char_data, headers={"Content-Type": "application/json", "Authorization": token}, method="POST")
            char_resp = urllib.request.urlopen(char_req, timeout=10)
            char_result = json.loads(char_resp.read())
            if char_result.get("code") != 200:
                self._respond(500, "Character creation failed: " + char_result.get("message", "UNKNOWN"))
                return

            # Step 4: Finalize (MongoDB fixes)
            script = FIX_FIELDS_SCRIPT % username
            fix_result = subprocess.run(
                ["mongosh", "go2super", "-u", "galaxybot", "-p", "Hak4oYk44ZahfRrepkFc", "--quiet", "--eval", script],
                capture_output=True, text=True, timeout=30, env={**os.environ, "HOME": "/root"}
            )
            output = fix_result.stdout.strip()

            uid_msg = ""
            fix_msg = ""
            needs_restart = False
            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("USERID_FIX:"):
                    uid_msg = line.replace("USERID_FIX:", "")
                    needs_restart = True
                elif line.startswith("FIXED:"):
                    fix_msg = line.replace("FIXED:", "")
                    needs_restart = True

            if needs_restart:
                subprocess.run(["sudo", "systemctl", "restart", "galaxybot-server"], capture_output=True, timeout=60)

            detail = {"username": username}
            if uid_msg:
                detail["userIdChanged"] = uid_msg
            if fix_msg:
                detail["fixed"] = fix_msg

            self._respond(200, "Account fully created", detail)

        except urllib.error.HTTPError as e:
            body = e.read()
            try:
                err = json.loads(body)
                self._respond(500, "HTTP error: " + err.get("message", str(e)))
            except json.JSONDecodeError:
                self._respond(500, "HTTP error: " + str(e))
        except subprocess.TimeoutExpired:
            self._respond(500, "Finalize timed out (MongoDB)")
        except Exception as e:
            self._respond(500, "Error: " + str(e))

    def _handle_list(self):
        try:
            result = subprocess.run(
                ["mongosh", "go2super", "-u", "galaxybot", "-p", "Hak4oYk44ZahfRrepkFc",
                 "--quiet", "--eval", """
                    var accounts = [];
                    db.game_users.find().sort({userId:1}).forEach(function(u) {
                        var p = db.game_planets.findOne({type:"USER_PLANET", userId: NumberInt(u.userId.valueOf())});
                        accounts.push({
                            username: u.username,
                            userId: NumberInt(u.userId.valueOf()),
                            guid: u.guid,
                            ground: u.ground,
                            planet: p ? "YES " + JSON.stringify(p.position) : "NONE"
                        });
                    });
                    print(JSON.stringify(accounts));
                """],
                capture_output=True, text=True, timeout=15,
                env={**os.environ, "HOME": "/root"}
            )
            output = result.stdout.strip()
            accounts = json.loads(output) if output else []
            self._respond(200, "OK", {"accounts": accounts, "count": len(accounts)})
        except Exception as e:
            self._respond(500, "LIST_ERROR", str(e))

    def _handle_finalize(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        username = body.get("username", "")
        if not username:
            self._respond(400, "MISSING_USERNAME")
            return

        try:
            script = FIX_FIELDS_SCRIPT % username
            result = subprocess.run(
                ["mongosh", "go2super", "-u", "galaxybot", "-p", "Hak4oYk44ZahfRrepkFc", "--quiet", "--eval", script],
                capture_output=True, text=True, timeout=30, env={**os.environ, "HOME": "/root"}
            )
            output = result.stdout.strip()
            if "USER_NOT_FOUND" in output:
                self._respond(404, "USER_NOT_FOUND", f"No user '{username}' in database")
                return

            fix_msg = ""
            uid_msg = ""
            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("FIXED:"):
                    fix_msg = line.replace("FIXED:", "")
                elif line.startswith("USERID_FIX:"):
                    uid_msg = line.replace("USERID_FIX:", "")
                elif line == "NO_FIX_NEEDED":
                    fix_msg = "none needed"

            message = "Account finalised"
            needs_restart = bool(uid_msg) or (fix_msg and fix_msg != "none needed")
            if needs_restart:
                subprocess.run(["sudo", "systemctl", "restart", "galaxybot-server"], capture_output=True, timeout=60)
                message += ", server restarted"
            else:
                message += " (no changes needed)"

            self._respond(200, message, {"fixed": fix_msg, "userIdChanged": uid_msg})

        except subprocess.TimeoutExpired:
            self._respond(500, "TIMEOUT", "MongoDB script timed out")
        except Exception as e:
            self._respond(500, "FINALIZE_ERROR", str(e))

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
        if len(args) >= 3:
            print(f"[admin-register] {args[0]} {args[1]} {args[2]}")
        else:
            print(f"[admin-register] {format}")

if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except:
        ip = "127.0.0.1"
    AdminRegisterHandler.server_ip = ip

    server = HTTPServer(("0.0.0.0", 9191), AdminRegisterHandler)
    print(f"Account creation service listening on http://0.0.0.0:9191")
    print(f"Open http://{ip}:9191/ in your browser to create accounts")
    server.serve_forever()
