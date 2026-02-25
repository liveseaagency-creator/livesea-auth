import os
import secrets
import requests
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse

app = FastAPI()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "")

GUILD_ID = os.getenv("GUILD_ID", "")
ROLE_ID = os.getenv("ROLE_ID", "")

@app.get("/")
def home():
    return {"status": "LiveSea Auth Server Online"}

@app.get("/login")
def login():
    if not CLIENT_ID or not REDIRECT_URI:
        return {"error": "Missing OAuth configuration"}

    url = (
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=identify%20guilds%20guilds.members.read"
        "&prompt=consent"
    )
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str = ""):
    if not code:
        return {"error": "Missing code"}

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
        return {"error": "Token exchange failed", "detail": token_json}

    user_res = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    user = user_res.json()
    user_id = user.get("id")

    member_res = requests.get(
        f"https://discord.com/api/users/@me/guilds/{GUILD_ID}/member",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if member_res.status_code != 200:
        return {"status": "DENIED", "reason": "Not in guild"}

    member = member_res.json()

    if ROLE_ID not in member.get("roles", []):
        return {"status": "DENIED", "reason": "Missing role"}

    session_token = secrets.token_urlsafe(24)

    return {
        "status": "AUTHORIZED",
        "discord_id": user_id,
        "token": session_token
    }
