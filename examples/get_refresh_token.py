#!/usr/bin/env python3
"""Local OAuth helper to get Google Business Profile refresh token and account IDs."""

import json
import os
import sys
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

CLIENT_ID = os.environ.get("GBP_OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GBP_OAUTH_CLIENT_SECRET", "")
REDIRECT_URI = "http://127.0.0.1:8080/"
SCOPE = "https://www.googleapis.com/auth/business.manage"

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ Error: Set GBP_OAUTH_CLIENT_ID and GBP_OAUTH_CLIENT_SECRET in your environment.")
    sys.exit(1)

auth_code = None


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in query_components:
            auth_code = query_components["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                    <h1 style="color: #2e7d32;">&#9989; Google Business Profile Authorization Successful!</h1>
                    <p>You can close this tab and return to your terminal/assistant.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed.")

    def log_message(self, format, *args):
        pass


def exchange_code(code: str) -> dict:
    url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    print("\n" + "=" * 75)
    print("🔑 GOOGLE BUSINESS PROFILE OAUTH AUTHORIZATION")
    print("=" * 75)
    print("\nPlease open this link in your browser if it doesn't open automatically:")
    print(f"\n{auth_url}\n")
    print("=" * 75)

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    server = HTTPServer(("127.0.0.1", 8080), OAuthHandler)
    print("\n⏳ Listening for Google authorization on http://127.0.0.1:8080/ ...")
    server.handle_request()

    if not auth_code:
        print("❌ Did not receive authorization code.")
        return

    print("🔄 Exchanging code for tokens...")
    tokens = exchange_code(auth_code)
    refresh_token = tokens.get("refresh_token")

    print("\n" + "=" * 75)
    print("🎉 SUCCESS! YOUR TOKENS ARE READY:")
    print("=" * 75)
    print(f"GBP_OAUTH_REFRESH_TOKEN={refresh_token}")
    print("=" * 75)


if __name__ == "__main__":
    main()
