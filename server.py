import os
import time
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

AUTHORIZED_UNTIL = 0


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
    global AUTHORIZED_UNTIL

    if not code:
        return HTMLResponse("<h2 style='color:red'>Code OAuth manquant</h2>")

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

    if token_res.status_code != 200:
        return HTMLResponse("<h2 style='color:red'>Erreur OAuth Discord</h2>")

    access_token = token_res.json().get("access_token")

    if not access_token:
        return HTMLResponse("<h2 style='color:red'>Token invalide</h2>")

    user_res = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if user_res.status_code != 200:
        return HTMLResponse("<h2 style='color:red'>Impossible de récupérer l'utilisateur</h2>")

    user_id = user_res.json().get("id")

    member_res = requests.get(
        f"https://discord.com/api/guilds/{GUILD_ID}/members/{user_id}",
        headers={"Authorization": f"Bot {BOT_TOKEN}"}
    )

    server_ok = member_res.status_code == 200
    roles = member_res.json().get("roles", []) if server_ok else []
    role_ok = ROLE_ID in roles
    access_ok = server_ok and role_ok

    if access_ok:
        AUTHORIZED_UNTIL = time.time() + 30
    else:
        AUTHORIZED_UNTIL = 0

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
    <meta charset="UTF-8">
    <title>LiveSea Auth</title>
    <style>
        body {{
            margin: 0;
            background: linear-gradient(135deg, #0f0f0f, #1c1c1c);
            font-family: 'Segoe UI', sans-serif;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}

        .card {{
            background: #181818;
            padding: 50px;
            border-radius: 20px;
            width: 520px;
            box-shadow: 0 0 40px rgba(0,255,150,0.2);
            text-align: center;
            animation: fadeIn 0.5s ease-in-out;
        }}

        h1 {{
            margin-bottom: 35px;
            font-size: 26px;
            color: {'#00ff88' if access_ok else '#ff3b3b'};
        }}

        .status {{
            display: flex;
            justify-content: space-between;
            margin: 12px 0;
            padding: 14px 20px;
            background: #111;
            border-radius: 10px;
            font-size: 15px;
        }}

        .ok {{
            color: #00ff88;
            font-weight: bold;
        }}

        .fail {{
            color: #ff3b3b;
            font-weight: bold;
        }}

        .footer {{
            margin-top: 30px;
            font-size: 14px;
            opacity: 0.7;
        }}
    </style>
    </head>
    <body>
    <div class="card">
        <h1>{'ACCÈS AUTORISÉ' if access_ok else 'ACCÈS REFUSÉ'}</h1>
        <div class="footer">
            {"Vous pouvez retourner sur Plutonium." if access_ok else "Rejoignez le serveur et obtenez le rôle requis."}
        </div>
    </div>
    </body>
    </html>
    """

    return HTMLResponse(html_content)


@app.get("/check")
def check():
    global AUTHORIZED_UNTIL

    if time.time() < AUTHORIZED_UNTIL:
        AUTHORIZED_UNTIL = 0
        return JSONResponse({"authorized": True})

    return JSONResponse({"authorized": False})
