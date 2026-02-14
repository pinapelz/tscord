import requests
from dotenv import load_dotenv
import os

load_dotenv()

WEB_QUERY_API = os.environ.get("WEB_QUERY_URL", "")
API_KEY = os.environ.get("API_KEY", "")

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")

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
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages?limit=1"
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.ok:
        messages = resp.json()
        return messages[0] if messages else None
    else:
        print(f"Failed to fetch messages: {resp.status_code} {resp.text}")
        return None

def edit_or_send_message(clients):
    client_names = "\n".join(f"- {c.get('client_nickname')}" for c in clients)
    content = f"\n**Users currently in Teamspeak:**\n{client_names}" if clients else "\nNo users online"

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
    update_discord_channel_name(clients)

if __name__ == "__main__":
    main()
