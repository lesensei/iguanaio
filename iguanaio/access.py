import asyncio
import re
import socket
import aiohttp
import async_timeout
import logging
from urllib.parse import urljoin

_LOGGER = logging.getLogger(__package__)


class Access:
    """Connection control."""

    def __init__(
        self, session: aiohttp.ClientSession, base_url, username, password, timeout
    ):
        """Init class."""
        self.session = session
        self.base_url = base_url
        self.rest_url = urljoin(self.base_url, "/iguana/Rest.Server.cls")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.sessionUrlId = None
        self.sessionJsonId = None
        self.mainUserId = None

    async def is_authenticated(self) -> bool:
        """Check if session is authenticated to the Iguana-IDM instance"""
        if self.sessionUrlId == None or self.sessionJsonId == None:
            return False
        params = {"sessionId": self.sessionUrlId, "method": "user/summary"}
        data = {"request": {"sessionId": self.sessionJsonId}}
        res = await self.api_wrapper(
            "post",
            self.rest_url,
            params=params,
            data=data,
        )
        _LOGGER.debug("res: %s", res)
        _LOGGER.debug("req: %s", res.request_info)
        if res.status != 200:
            return False
        info: dict = await res.json(content_type="text/html")
        _LOGGER.debug("JSON result: '%s'", info)
        return True

    async def authenticate(self) -> bool:
        """Authenticate to the Iguana-IDM instance"""
        if await self.is_authenticated():
            return True
        # Get the necessary cookies (in my testing, both GETs seemed to be needed)
        res = await self.api_wrapper(
            "get", urljoin(self.base_url, "/iguana/www.main.cls")
        )
        _LOGGER.debug("res: %s", res)
        _LOGGER.debug("req: %s", res.request_info)
        homeHtml = await res.text()
        self.sessionUrlId = re.search(r"sessionID = '(\w+)'", homeHtml).group(1)
        _LOGGER.debug("sessionUrlId: %s", self.sessionUrlId)
        # POST login information
        res = await self.api_wrapper(
            "post",
            self.rest_url,
            params={"sessionId": self.sessionUrlId, "method": "user/credentials"},
            data={
                "request": {
                    "language": "fre",
                    "serviceProfile": "Iguana",
                    "locationProfile": "",
                    "user": self.username,
                    "password": self.password,
                    "institution": "",
                }
            },
        )
        _LOGGER.debug("res: %s", res)
        _LOGGER.debug("req: %s", res.request_info)
        if res.status != 200:
            return False
        info: dict = await res.json(content_type="text/html")
        _LOGGER.debug("JSON result: '%s'", info)
        self.sessionJsonId = info["response"]["sessionId"]
        self.mainUserId = info["response"]["borrowerId"]
        _LOGGER.debug("sessionJsonId: '%s'", self.sessionJsonId)
        return await self.is_authenticated()

    async def api_call(
        self, endpoint: str, request: dict = {}
    ) -> aiohttp.ClientResponse:
        """Call an API endpoint"""
        try:
            params = {
                "sessionId": self.sessionUrlId,
                "method": f"user/{endpoint}",
            }
            data = {
                "request": {
                    "sessionId": self.sessionJsonId,
                }
                | request
            }
            _LOGGER.debug(
                "Posting to '%s' with params '%s' and data '%s'",
                self.rest_url,
                params,
                data,
            )

            return await self.api_wrapper(
                "post", self.rest_url, data=data, params=params
            )
        except Exception as ex:
            _LOGGER.error("Something really wrong happened! - %s", ex)
            raise

    async def api_wrapper(
        self,
        method: str,
        url: str,
        data: dict = {},
        headers: dict = {},
        params: dict = {},
    ) -> aiohttp.ClientResponse:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(self.timeout):
                if method == "get":
                    return await self.session.get(
                        url, headers=headers, params=params, allow_redirects=False
                    )

                elif method == "post":
                    return await self.session.request(
                        aiohttp.hdrs.METH_POST,
                        url,
                        headers=headers,
                        params=params,
                        json=data,
                        allow_redirects=False,
                    )

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )
            raise

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
            raise

        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
            raise

        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
            raise
