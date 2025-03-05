from quart import websocket

from app.config.settings import settings

active_connections_st = set()

import aiohttp

SLACK_CHANNEL = "#classroom-notifications"


async def broadcast_to_admins(message: str):
  for conn in list(active_connections_st):
    try:
      await conn.send(message)
    except Exception:
      active_connections_st.remove(conn)


async def send_slack_message(text: str):
  url = "https://slack.com/api/chat.postMessage"
  headers = {"Authorization": f"Bearer {settings.SLACK_BOT_KEY}", "Content-Type": "application/json"}
  payload = {"channel": SLACK_CHANNEL, "text": text}

  try:
    async with aiohttp.ClientSession() as session:
      async with session.post(url, headers=headers, json=payload) as resp:
        status = resp.status
        response_data = await resp.json()

        if status != 200:
          await websocket.send_json({"success": False, "error": f"HTTP {status}"})

        if not response_data.get("ok"):
          error_message = response_data.get("error", "Unknown error")
          await websocket.send_json({"success": False, "error": error_message})

        await websocket.send_json({"success": True, "response": response_data})

  except aiohttp.ClientError as e:
    await websocket.send_json({"success": False, "error": "Request failed"})
  except Exception as e:
    await websocket.send_json({"success": False, "error": "Unexpected error"})
