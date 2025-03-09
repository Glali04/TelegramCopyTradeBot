"""
i will make a client session for each server i connect my program, there will be 3 (dexscrenner, birdeye, jupiter)
this sessions will live while my program is running that is more efficient then oppening new session for every request
i made to servers.
"""
import aiohttp
import asyncio
from datetime import datetime
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed


class HTTPClient:
    def __init__(self):
        self.sessions = {}  # stores session for different servers

    async def start_session(self, base_url):
        """True if the session has been closed, False otherwise. if we call it on ClientSession"""
        if base_url not in self.sessions or self.sessions[base_url].closed:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            self.sessions[base_url] = aiohttp.ClientSession(base_url=base_url, timeout=aiohttp.ClientTimeout(1),
                                                            headers=headers)

    async def fetch(self, base_url, endpoint, params=None, data=None, swap_endpoint=False):
        """Fetch data from API with retries and error handling."""
        await self.start_session(base_url)
        session = self.sessions[base_url]

        error_information = f"Occurred: {datetime.now()}, on server: {base_url}/{endpoint}"

        async for attempt in AsyncRetrying(stop=stop_after_attempt(2), wait=wait_fixed(1.0)):
            with attempt:
                try:
                    if not swap_endpoint:
                        async with session.get(f"/{endpoint}", params=params) as response:
                            response.raise_for_status()
                            return await response.json()
                    else:
                        async with session.post(f"/{endpoint}", params=params, data=data) as response:
                            response.raise_for_status()
                            return await response.json()

                except aiohttp.ClientConnectionError:
                    print(f"Network error! {error_information}")

                except aiohttp.ClientTimeout:
                    print(f"API took too long! {error_information}")

                except aiohttp.ClientResponseError as e:
                    if e.status == 429:  # Rate Limited
                        print(f"Rate limited! Sleeping for 1s, {error_information}")
                        await asyncio.sleep(1)  # Non-blocking sleep
                    elif e.status >= 500:  # Server Errors
                        print(f"Server error! {error_information}")
        # If all retry attempts fail, return None
        return None

    async def close(self):
        for session in self.sessions.values():
            if session and not session.closed:
                await session.close()
        self.sessions.clear()


# Global instance of HTTPClient
http_client = HTTPClient()
