import asyncio
import json

import requests
import websockets


class KickClient:

    def __init__(self, auth_token=None, channel_id=None):
        self.api_base_url = "https://api.kick.com/v2"
        self.ws_base_url = "wss://ws-us-1.pusher.com/app/eb1d5f283081a78b932c?protocol=7&client=js&version=7.0.3&flash=false"
        self.auth_token = auth_token
        self.channel_id = channel_id
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}" if self.auth_token else "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_clip(self, title=None, duration=60):
        """Creates a clip of the current livestream."""
        if not self.channel_id:
            raise ValueError("Channel ID is required to create a clip.")

        endpoint = f"/channels/{self.channel_id}/clips"
        url = self.api_base_url + endpoint

        payload = {
            "title": title,
            "duration": duration,
        }

        # Filter out None values
        payload = {k: v for k, v in payload.items() if v is not None}

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    async def listen_for_clip_events(self, on_clip_created):
        """Connects to the websocket and listens for clip.created events."""
        if not self.channel_id:
            raise ValueError("Channel ID is required to listen for events.")

        uri = self.ws_base_url

        async with websockets.connect(uri) as websocket:
            # Subscribe to the channel's clips events
            await websocket.send(
                json.dumps({
                    "event": "pusher:subscribe",
                    "data": {
                        "channel": f"channel.{self.channel_id}"
                    },
                }))

            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if data.get("event") == "clip.created":
                    if on_clip_created:
                        await on_clip_created(data.get("data"))
