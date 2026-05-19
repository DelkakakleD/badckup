#!/usr/bin/env python3
"""
GalaxyBot Account Creator — Interactive TUI
Creates fully playable accounts (account + character + planet + fixes) in one go.
"""
import json
import os
import sys
import urllib.request
import urllib.error

SERVER = os.environ.get("GAME_SERVER", "http://127.0.0.1:9090")
ADMIN_SERVER = os.environ.get("ADMIN_SERVER", "http://127.0.0.1:9191")


def clear():
    os.system("clear" if os.name == "posix" else "cls")


def print_header(title):
    w = 58
    print(" " + "=" * w)
    print(f"   {title}")
    print(" " + "=" * w)


def menu(options, prompt="Select an option"):
    print()
    for i, (key, label) in enumerate(options, 1):
        print(f"  [{i}] {label}")
    print()
    while True:
        try:
            choice = input(f"  {prompt} [1-{len(options)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        except (ValueError, IndexError):
            pass
        print(f"  Invalid choice. Enter 1-{len(options)}.")


def confirm(prompt):
    return input(f"\n  {prompt} (y/n): ").strip().lower() == "y"


def api_call(url, data=None, method="POST", timeout=120):
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"code": e.code, "message": str(e)}
    except Exception as e:
        return {"code": 500, "message": str(e)}


def create_account():
    clear()
    print_header("Create New Account")

    username = input("  Username: ").strip()
    if not username:
        input("  Username required. Press Enter...")
        return

    password = input("  Password: ").strip()
    if not password:
        input("  Password required. Press Enter...")
        return

    email = input("  Email: ").strip()
    if not email:
        email = f"{username.lower()}@game.com"
        print(f"  (using {email})")

    if not confirm(f'Create account "{username}"?'):
        return

    print(f"\n  Creating account...")
    result = api_call(f"{ADMIN_SERVER}/admin/create", {
        "username": username,
        "password": password,
        "email": email,
    })

    print()
    if result.get("code") == 200:
        detail = result.get("detail", {})
        print(f"  ✅ Account '{username}' fully created!")
        print(f"     Password: {password}")
        print(f"     Login:    {SERVER}/login/login/account")
        if detail.get("userIdChanged"):
            print(f"     userId:   {detail['userIdChanged']}")
        if detail.get("fixed"):
            print(f"     Fixed:    {detail['fixed']}")
        print(f"\n     Server restarting (~25s)... wait before logging in.")
    else:
        print(f"  ❌ Failed: {result.get('message', 'Unknown error')}")

    input("\n  Press Enter to continue...")


def list_accounts():
    clear()
    print_header("All Accounts")

    try:
        result = api_call(f"{ADMIN_SERVER}/admin/list", method="GET", timeout=10)
        if result.get("code") == 200:
            accounts = result.get("detail", {}).get("accounts", [])
            if accounts:
                print(f"  {'Username':<18} {'UserId':<8} {'GUID':<10} {'Planet':<20}")
                print(f"  {'-'*18} {'-'*8} {'-'*10} {'-'*20}")
                for a in accounts:
                    planet = a.get("planet", "NONE")
                    print(f"  {a['username']:<18} {str(a.get('userId', '?')):<8} {str(a.get('guid', '?')):<10} {planet:<20}")
            else:
                print("  No accounts found.")
        else:
            # Fallback: direct mongosh
            import subprocess
            r = subprocess.run(
                ["mongosh", "go2super", "-u", "galaxybot", "-p", "Hak4oYk44ZahfRrepkFc",
                 "--quiet", "--eval", """
                    db.game_users.find().sort({userId:1}).forEach(function(u) {
                        var p = db.game_planets.findOne({type:"USER_PLANET", userId: NumberInt(u.userId.valueOf())});
                        print(u.username + "|" + u.userId.valueOf() + "|" + u.guid + "|" + (p ? "YES" : "NO"));
                    });
                 """],
                capture_output=True, text=True, timeout=10
            )
            print(f"  {'Username':<18} {'UserId':<8} {'GUID':<10} {'Planet'}")
            print(f"  {'-'*18} {'-'*8} {'-'*10} {'-'*6}")
            for line in r.stdout.strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 4:
                    print(f"  {parts[0]:<18} {parts[1]:<8} {parts[2]:<10} {parts[3]}")
    except Exception as e:
        print(f"  Error: {e}")

    input("\n  Press Enter to continue...")


def health_check():
    clear()
    print_header("Server Health")

    try:
        r = urllib.request.urlopen(f"{SERVER}/health", timeout=5)
        d = json.loads(r.read()).get("data", {})
        print(f"  Status:     ✅ UP")
        print(f"  Players:    {d.get('onlinePlayers', 0)}")
        print(f"  Uptime:     {d.get('uptimeMs', 0) // 1000}s")
        print(f"  Memory:     {d.get('heapUsedMB', '?')}MB / {d.get('heapMaxMB', '?')}MB")
        print(f"  Threads:    {d.get('threads', '?')}")
        print(f"  Maintenance: {'ON' if d.get('maintenance') else 'OFF'}")
    except Exception:
        print(f"  Server:     ❌ DOWN")

    try:
        r = urllib.request.urlopen(f"{ADMIN_SERVER}/admin/health", timeout=5)
        print(f"  Admin API:  ✅ UP")
    except Exception:
        print(f"  Admin API:  ❌ DOWN")

    input("\n  Press Enter to continue...")


def main():
    while True:
        clear()
        print_header("GalaxyBot Account Creator")
        print(f"  Game server:  {SERVER}")
        print(f"  Admin server: {ADMIN_SERVER}")
        print()

        action = menu([
            ("create", "Create new account"),
            ("list", "List all accounts"),
            ("health", "Server health check"),
            ("exit", "Exit"),
        ], "Choose action")

        if action == "create":
            create_account()
        elif action == "list":
            list_accounts()
        elif action == "health":
            health_check()
        elif action == "exit":
            clear()
            print("Goodbye!\n")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        print("\nGoodbye!\n")
        sys.exit(0)
