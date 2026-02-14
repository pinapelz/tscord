import requests
from dotenv import load_dotenv
import os

load_dotenv()

WEB_QUERY_API = os.environ.get("WEB_QUERY_URL", "")
API_KEY = os.environ.get("API_KEY", "")

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")
ATTACH_AFK_STATUS = True
ATTTACH_STREAMING_STATUS = True

def fetch_clients():
    headers = {"x-api-key": API_KEY}
    try:
        response = requests.get(f"{WEB_QUERY_API}/1/clientlist", headers=headers, timeout=5)
        response.raise_for_status()
        clients = response.json().get('body', [])
        return [c for c in clients if c.get("client_nickname") != "serveradmin"]
    except requests.exceptions.RequestException as e:
        print(f"Couldn't fetch client list: {e}")
        return []

def get_last_message():
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
    limit = 100  # max allowed by Discord API
    params = {"limit": limit}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            return None
        while len(batch) == limit:
            oldest_id = batch[-1]["id"]
            params["before"] = oldest_id
            resp = requests.get(url, headers=headers, params=params, timeout=5)
            resp.raise_for_status()
            new_batch = resp.json()
            if not new_batch:
                break
            batch = new_batch
        return batch[-1] if batch else None

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch messages: {e}")
        return None

def edit_or_send_message(clients):
    client_lines = []
    api_headers = {"x-api-key": API_KEY}
    for c in clients:
        clid = c.get("clid")
        nickname = c.get("client_nickname")
        afk_text = ""
        stream_text = ""
        if clid and (ATTACH_AFK_STATUS or ATTTACH_STREAMING_STATUS):
            try:
                resp = requests.get(f"{WEB_QUERY_API}/1/clientinfo?clid={clid}", headers=api_headers, timeout=5)
                resp.raise_for_status()
                body = resp.json().get("body", [])
                info = body[0] if isinstance(body, list) and body else {}
                if ATTACH_AFK_STATUS and info.get("client_away") == "1":
                    away_msg = info.get("client_away_message", "")
                    afk_text = f" (**CURRENTLY AFK:** `{away_msg}`)" if away_msg else " (**CURRENTLY AFK**)"
                if ATTTACH_STREAMING_STATUS and info.get("client_streaming") == "1":
                    stream_text = " **[STREAMING]**"
            except requests.exceptions.RequestException as e:
                print(f"Couldn't fetch client info for {clid}: {e}")

        client_lines.append(f"- {nickname}{afk_text}{stream_text}")
    client_names = "\n".join(client_lines)
    content = f"# **Users currently in Teamspeak:** \n{client_names}" if client_lines else "\nNo users online"

    last_msg = get_last_message()
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json"}

    if last_msg:
        # Edit the last message
        url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages/{last_msg['id']}"
        resp = requests.patch(url, headers=headers, json={"content": content})
        if resp.ok:
            print("Discord message edited")
        else:
            print(f"Failed to edit message: {resp.status_code} {resp.text}")
    else:
        # Send a new message
        url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
        resp = requests.post(url, headers=headers, json={"content": content})
        if resp.ok:
            print("Discord message sent")
        else:
            print(f"Failed to send message: {resp.status_code} {resp.text}")

def update_discord_channel_name(clients):
    count = len(clients)
    new_name = f"teamspeak-{count}"

    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"name": new_name}

    resp = requests.patch(url, headers=headers, json=payload)
    if resp.ok:
        print(f"Channel renamed to {new_name}")
    else:
        print(f"Failed to rename channel: {resp.status_code} {resp.text}")

def main():
    clients = fetch_clients()
    edit_or_send_message(clients)
    #update_discord_channel_name(clients)

if __name__ == "__main__":
    main()
