"""One-time local Google Drive OAuth setup for ENGINEER OS.

Run on the user's Windows PC. The script opens Google's consent page, receives
the localhost callback, exchanges the code, and writes a gitignored env file.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
from urllib import parse, request
import webbrowser


SCOPE = "https://www.googleapis.com/auth/drive.readonly"
PORT = 8765
REDIRECT_URI = f"http://127.0.0.1:{PORT}/callback"


def main() -> None:
    client_id = os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise SystemExit(
            "Set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET before running this script."
        )

    state = secrets.token_urlsafe(32)
    result: dict[str, str] = {}

    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = parse.urlparse(self.path)
            query = parse.parse_qs(parsed.query)
            if parsed.path != "/callback" or query.get("state", [""])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid OAuth callback.")
                return
            code = query.get("code", [""])[0]
            if not code:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Google authorization was not completed.")
                return
            result["code"] = code
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Google Drive connected. You can close this tab.".encode("utf-8"))

        def log_message(self, format, *args):
            return

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + parse.urlencode(params)
    print("Opening Google authorization in your browser...")
    webbrowser.open(auth_url)

    server = HTTPServer(("127.0.0.1", PORT), Callback)
    while "code" not in result:
        server.handle_request()
    server.server_close()

    token_payload = parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": result["code"],
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }).encode("ascii")
    req = request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with request.urlopen(req, timeout=30) as response:
        tokens = json.loads(response.read().decode("utf-8"))
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise SystemExit("Google did not return a refresh token. Re-run and approve offline access.")

    output = Path(".env.google-drive")
    output.write_text(
        "GOOGLE_DRIVE_CLIENT_ID=" + client_id + "\n"
        "GOOGLE_DRIVE_CLIENT_SECRET=" + client_secret + "\n"
        "GOOGLE_DRIVE_REFRESH_TOKEN=" + refresh_token + "\n",
        encoding="utf-8",
    )
    print("Google Drive OAuth complete. Secrets saved to .env.google-drive (gitignored).")


if __name__ == "__main__":
    main()
