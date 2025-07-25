import asyncio
import json
import logging

import requests
import websockets

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
        logger.info("KickClient initialized for channel ID: %s", self.channel_id)

    def create_clip(self, title=None, duration=60):
        """Creates a clip of the current livestream."""
        if not self.channel_id:
            logger.error("Channel ID is required to create a clip. Aborting clip creation.")
            raise ValueError("Channel ID is required to create a clip.")

        endpoint = f"/channels/{self.channel_id}/clips"
        url = self.api_base_url + endpoint

        payload = {
            "title": title,
            "duration": duration,
        }

        # Filter out None values
        payload = {k: v for k, v in payload.items() if v is not None}
        logger.info("Attempting to create clip for channel %s with payload: %s", self.channel_id, payload)

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(
                "Clip created successfully for channel %s. Response: %s", self.channel_id, response.json())
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Error creating clip for channel %s: %s", self.channel_id, e)
            raise

    async def listen_for_clip_events(self, on_clip_created):
        """Connects to the websocket and listens for clip.created events."""
        if not self.channel_id:
            logger.error("Channel ID is required to listen for events. Aborting event listener.")
            raise ValueError("Channel ID is required to listen for events.")

        uri = self.ws_base_url
        logger.info("Connecting to websocket for channel ID: %s at %s", self.channel_id, uri)

        try:
            async with websockets.connect(uri) as websocket:
                # Subscribe to the channel's clips events
                subscribe_message = json.dumps({
                    "event": "pusher:subscribe",
                    "data": {
                        "channel": f"channel.{self.channel_id}"
                    },
                })
                await websocket.send(subscribe_message)
                logger.info("Subscribed to channel %s for clip events.", self.channel_id)

                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    logger.debug("Received websocket message: %s", data)

                    if data.get("event") == "clip.created":
                        clip_data = data.get("data")
                        logger.info(
                            "Clip created event received for channel %s: %s", self.channel_id, clip_data)
                        if on_clip_created:
                            await on_clip_created(clip_data)
        except websockets.exceptions.WebSocketException as e:
            logger.error("Websocket error for channel %s: %s", self.channel_id, e)
            raise
        except Exception as e:
            logger.critical(
                "An unexpected error occurred in listen_for_clip_events for channel %s: %s", self.channel_id,
                e)
            raise
