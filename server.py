import os
import requests
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse

app = FastAPI()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

GUILD_ID = os.getenv("GUILD_ID")
ROLE_ID = os.getenv("ROLE_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

AUTHORIZED_USERS = set()

@app.get("/")
def home():
    return {"status": "LiveSea Auth Online"}

@app.get("/login")
def login():
    url = (
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=identify"
    )
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str = ""):

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

    access_token = token_res.json().get("access_token")

    user_res = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    user_id = user_res.json().get("id")

    member_res = requests.get(
        f"https://discord.com/api/guilds/{GUILD_ID}/members/{user_id}",
        headers={"Authorization": f"Bot {BOT_TOKEN}"}
    )

    if member_res.status_code != 200:
        return HTMLResponse("<h2 style='color:red'>NOT IN DISCORD SERVER</h2>")

    roles = member_res.json().get("roles", [])

    if ROLE_ID not in roles:
        return HTMLResponse("<h2 style='color:red'>MISSING ROLE</h2>")

    AUTHORIZED_USERS.add(user_id)

    return HTMLResponse("""
    <html>
    <head>
    <style>
    body { background:#0f0f0f; color:white; font-family:Arial; text-align:center; padding-top:100px;}
    .box {background:#1a1a1a;padding:40px;border-radius:12px;display:inline-block;box-shadow:0 0 25px #00ff88;}
    .ok {color:#00ff88;font-size:20px;}
    </style>
    </head>
    <body>
    <div class="box">
    <h1>LIVESEA AUTH SUCCESS</h1>
    <div class="ok">ROLE DISCORD : OK</div>
    <div class="ok">SERVEUR DISCORD : OK</div>
    <div class="ok">ACCES : OK</div>
    </div>
    </body>
    </html>
    """)

@app.get("/check")
def check():
    if len(AUTHORIZED_USERS) > 0:
        AUTHORIZED_USERS.clear()
        return {"authorized": True}
    return {"authorized": False}
