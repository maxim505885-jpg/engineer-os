"""One-time local Google Drive OAuth setup for ENGINEER OS.

Desktop OAuth uses a free loopback port and PKCE. A client secret is not
required for this installed-app flow.
"""

from __future__ import annotations

import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
from urllib import error, parse, request
import webbrowser

SCOPE = "https://www.googleapis.com/auth/drive.readonly"


def main() -> None:
    client_id = os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "").strip()
    if not client_id:
        raise SystemExit("Set GOOGLE_DRIVE_CLIENT_ID before running this script.")

    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
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
            self.wfile.write(b"Google Drive connected. You can close this tab.")

        def log_message(self, format, *args):
            return

    server = HTTPServer(("127.0.0.1", 0), Callback)
    port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{port}/callback"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + parse.urlencode(params)

    print(f"OAuth callback listening on free local port {port}")
    print("Opening Google authorization in your browser...")
    webbrowser.open(auth_url)

    try:
        while "code" not in result:
            server.handle_request()
    finally:
        server.server_close()

    token_payload = parse.urlencode({
        "client_id": client_id,
        "code": result["code"],
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }).encode("ascii")
    req = request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            tokens = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
            safe_error = detail.get("error", "oauth_error")
            safe_description = detail.get("error_description", "")
        except Exception:
            safe_error, safe_description = "oauth_error", ""
        raise SystemExit(f"Google token exchange failed: {safe_error}: {safe_description}") from None

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise SystemExit("Google did not return a refresh token. Re-run and approve offline access.")

    output = Path(".env.google-drive")
    output.write_text(
        "GOOGLE_DRIVE_CLIENT_ID=" + client_id + "\n"
        "GOOGLE_DRIVE_REFRESH_TOKEN=" + refresh_token + "\n",
        encoding="utf-8",
    )
    print("Google Drive OAuth complete. Secrets saved to .env.google-drive (gitignored).")


if __name__ == "__main__":
    main()
