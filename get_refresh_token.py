#!/usr/bin/env python3
"""
Helper script to get Spotify refresh token
Run this script to obtain a refresh token for the Spotify Web API
"""
import urllib.parse
import base64
import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Get credentials from user
print("=" * 60)
print("Spotify Refresh Token Generator")
print("=" * 60)
print()
print("You need your Client ID and Client Secret from:")
print("https://developer.spotify.com/dashboard")
print()

CLIENT_ID = input("Enter your Client ID: ").strip()
CLIENT_SECRET = input("Enter your Client Secret: ").strip()
REDIRECT_URI = input("Enter your Redirect URI (default: http://localhost:8888/callback): ").strip() or "http://localhost:8888/callback"

# Scopes needed for reading currently playing track
SCOPES = "user-read-currently-playing user-read-playback-state"

# Step 1: Generate authorization URL
auth_url = "https://accounts.spotify.com/authorize"
params = {
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPES,
    "show_dialog": "false"
}

auth_url_with_params = f"{auth_url}?{urllib.parse.urlencode(params)}"

print()
print("=" * 60)
print("Step 1: Authorization")
print("=" * 60)
print(f"Opening browser to authorize...")
print(f"If browser doesn't open, visit this URL manually:")
print(auth_url_with_params)
print()

# Open browser
webbrowser.open(auth_url_with_params)

# Step 2: Start local server to receive callback
authorization_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_code
        if self.path.startswith("/callback"):
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in query_params:
                authorization_code = query_params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                    <head><title>Success</title></head>
                    <body>
                        <h1>Authorization successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                    </body>
                    </html>
                """)
            else:
                error = query_params.get("error", ["Unknown error"])[0]
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f"""
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h1>Authorization failed</h1>
                        <p>Error: {error}</p>
                    </body>
                    </html>
                """.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress server logs

# Extract port from redirect URI
port = urllib.parse.urlparse(REDIRECT_URI).port or 8888

print(f"Waiting for authorization callback on {REDIRECT_URI}...")
print("(Press Ctrl+C to cancel)")
print()

server = HTTPServer(("localhost", port), CallbackHandler)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

try:
    # Wait for authorization code (with timeout)
    import time
    timeout = 300  # 5 minutes
    start_time = time.time()
    while authorization_code is None:
        if time.time() - start_time > timeout:
            print("\nTimeout waiting for authorization. Please try again.")
            server.shutdown()
            exit(1)
        time.sleep(0.5)
    
    server.shutdown()
    
    print("Authorization code received!")
    print()
    
    # Step 3: Exchange authorization code for tokens
    print("=" * 60)
    print("Step 2: Getting Refresh Token")
    print("=" * 60)
    
    token_url = "https://accounts.spotify.com/api/token"
    
    # Prepare credentials
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": REDIRECT_URI
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    refresh_token = token_data["refresh_token"]
    access_token = token_data["access_token"]
    
    print()
    print("=" * 60)
    print("SUCCESS! Your refresh token:")
    print("=" * 60)
    print()
    print(refresh_token)
    print()
    print("=" * 60)
    print("Add this to your .env file as:")
    print("=" * 60)
    print(f"LISTENING_REFRESH_TOKEN={refresh_token}")
    print()
    print("Note: Keep this token secure and don't share it publicly!")
    print()

except KeyboardInterrupt:
    print("\n\nCancelled by user.")
    server.shutdown()
    exit(1)
except requests.exceptions.HTTPError as e:
    print(f"\nError getting refresh token: {e}")
    if e.response is not None:
        print(f"Response: {e.response.text}")
    server.shutdown()
    exit(1)
except Exception as e:
    print(f"\nUnexpected error: {e}")
    import traceback
    traceback.print_exc()
    server.shutdown()
    exit(1)

