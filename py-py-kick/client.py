import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

import requests
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class KickAPIError(Exception):
    """Custom exception for Kick API errors."""
    pass


class KickWebSocketError(Exception):
    """Custom exception for Kick WebSocket errors."""
    pass


class KickClient:
    """Pythonic client for interacting with the Kick API and receiving clip alerts."""

    def __init__(self, auth_token: Optional[str] = None, channel_id: Optional[str] = None) -> None:
        """
        Initialize the KickClient.

        :param auth_token: Bearer token for authentication.
        :param channel_id: Channel ID to interact with.
        """
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

    def create_clip(self, title: Optional[str] = None, duration: int = 60) -> Dict[str, Any]:
        """
        Create a clip of the current livestream.

        :param title: Optional title for the clip.
        :param duration: Duration of the clip in seconds.
        :return: JSON response from the API.
        :raises KickAPIError: If the API call fails.
        """
        if not self.channel_id:
            logger.error("Channel ID is required to create a clip. Aborting clip creation.")
            raise ValueError("Channel ID is required to create a clip.")

        endpoint = f"/channels/{self.channel_id}/clips"
        url = self.api_base_url + endpoint

        payload = {"title": title, "duration": duration}
        payload = {k: v for k, v in payload.items() if v is not None}
        logger.info("Attempting to create clip for channel %s with payload: %s", self.channel_id, payload)

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(
                "Clip created successfully for channel %s. Response: %s", self.channel_id, response.json())
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Timeout occurred while creating clip for channel %s.", self.channel_id)
            raise KickAPIError("Timeout occurred while creating clip.")
        except requests.exceptions.RequestException as e:
            logger.error("Error creating clip for channel %s: %s", self.channel_id, e)
            raise KickAPIError(f"Error creating clip: {e}")

    async def listen_for_clip_events(
        self,
        on_clip_created: Optional[Callable[[Dict[str, Any]], Awaitable[None]]],
    ) -> None:
        """
        Connect to the websocket and listen for clip.created events.

        :param on_clip_created: Async callback to handle clip.created events.
        :raises KickWebSocketError: If websocket connection fails.
        """
        if not self.channel_id:
            logger.error("Channel ID is required to listen for events. Aborting event listener.")
            raise ValueError("Channel ID is required to listen for events.")

        uri = self.ws_base_url
        logger.info("Connecting to websocket for channel ID: %s at %s", self.channel_id, uri)

        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
                subscribe_message = json.dumps({
                    "event": "pusher:subscribe",
                    "data": {
                        "channel": f"channel.{self.channel_id}"
                    },
                })
                await websocket.send(subscribe_message)
                logger.info("Subscribed to channel %s for clip events.", self.channel_id)

                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=60)
                        data = json.loads(message)
                        logger.debug("Received websocket message: %s", data)

                        if data.get("event") == "clip.created":
                            clip_data = data.get("data")
                            logger.info(
                                "Clip created event received for channel %s: %s", self.channel_id, clip_data)
                            if on_clip_created:
                                await on_clip_created(clip_data)
                    except asyncio.TimeoutError:
                        logger.warning(
                            "No message received from websocket for 60 seconds. Keeping connection alive.")
                        continue
        except websockets.exceptions.WebSocketException as e:
            logger.error("Websocket error for channel %s: %s", self.channel_id, e)
            raise KickWebSocketError(f"Websocket error: {e}")
        except Exception as e:
            logger.critical(
                "An unexpected error occurred in listen_for_clip_events for channel %s: %s", self.channel_id,
                e)
            raise KickWebSocketError(f"Unexpected error: {e}")
