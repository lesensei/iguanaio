import asyncio
import inspect
import socket
from urllib.parse import urlparse, urlunparse
import aiohttp
from iguanaio.access import Access

import iguanaio.api as Api

TIMEOUT = 10

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class IguanaClient:
    """Deals with Iguana-IDM API calls"""

    def __init__(
        self, url: str, username: str, password: str, session: aiohttp.ClientSession
    ):
        """Sample API Client."""
        self._access = None
        self._url = url
        self._username = username
        self._password = password
        self._session = session

    def _load_modules(self):
        """Instantiate modules."""
        for name in Api.__dict__.keys():
            obj = getattr(Api, name)
            if inspect.isclass(obj):
                setattr(self, name.lower(), obj(self._access))

    async def connect(self):
        self._access = Access(
            session=self._session,
            base_url=self._url,
            username=self._username,
            password=self._password,
            timeout=TIMEOUT,
        )

        if self._access:
            # pylint: disable=unused-variable
            try:
                await self._access.authenticate()
            except asyncio.TimeoutError as exception:
                raise
            except (KeyError, TypeError) as exception:
                raise
            except (aiohttp.ClientError, socket.gaierror) as exception:
                raise
            except Exception as exception:  # pylint: disable=broad-except
                raise

            self._load_modules()

        return await self._access.is_authenticated()
