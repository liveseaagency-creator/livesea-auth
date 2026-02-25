import os
import secrets
import requests
import time
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse

app = FastAPI()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "")

GUILD_ID = os.getenv("GUILD_ID", "")
ROLE_ID = os.getenv("ROLE_ID", "")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

TOKENS = {}

@app.get("/")
def home():
    return {"status": "LiveSea Auth Server Online"}

@app.get("/login")
def login():
    url = (
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=identify"
        "&prompt=consent"
    )
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str = ""):

    if not code:
        return JSONResponse({"error": "Missing code"}, status_code=400)

    token_res = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token_json = token_res.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return JSONResponse({"error": "Token exchange failed"}, status_code=400)

    user_res = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    user = user_res.json()
    user_id = user.get("id")

    if not user_id:
        return JSONResponse({"error": "User fetch failed"}, status_code=400)

    member_res = requests.get(
        f"https://discord.com/api/guilds/{GUILD_ID}/members/{user_id}",
        headers={"Authorization": f"Bot {BOT_TOKEN}"}
    )

    if member_res.status_code != 200:
        return JSONResponse({"status": "DENIED", "reason": "Not in guild"}, status_code=403)

    member = member_res.json()
    roles = member.get("roles", [])

    if ROLE_ID not in roles:
        return JSONResponse({"status": "DENIED", "reason": "Missing role"}, status_code=403)

    secure_token = secrets.token_urlsafe(32)

    TOKENS[secure_token] = {
        "user_id": user_id,
        "expires": time.time() + 300
    }

    return JSONResponse({"status": "OK", "token": secure_token})

@app.get("/verify")
def verify(token: str = ""):
    data = TOKENS.get(token)

    if not data:
        return JSONResponse({"valid": False}, status_code=403)

    if time.time() > data["expires"]:
        TOKENS.pop(token, None)
        return JSONResponse({"valid": False, "expired": True}, status_code=403)

    TOKENS.pop(token, None)

    return {"valid": True}
