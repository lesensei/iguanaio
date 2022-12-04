import logging
from typing import Any, List
from urllib.parse import urljoin

from iguanaio.access import Access

_LOGGER = logging.getLogger(__package__)


class Reservations:
    def __init__(self, access: Access):
        self._access = access

    async def get_reservations(self, offset: int = 0, size: int = 10):
        """Get current reservations"""
        if not await self._access.is_authenticated():
            await self._access.authenticate()
        data = {
            "LocationProfile": "",
            "range": {"from": offset + 1, "to": offset + size},
            "sort": {"sortBy": "!DueDate", "sortDirection": "ASC"},
        }
        res = await self._access.api_call("reservations", request=data)
        if res.status != 200:
            _LOGGER.error(
                "Error fetching Iguana-IDM user reservations: '%s'", res.reason
            )
            return
        return (await res.json(content_type="text/html"))["response"]

    async def get_linked_reservations(
        self, user: str = None, offset: int = 0, size: int = 50
    ):
        """Get linked account(s) reservations"""
        if not await self._access.is_authenticated():
            await self._access.authenticate()
        data = {
            "userId": user,
        }
        res = await self._access.api_call("switchuser", request=data)
        if res.status != 200:
            _LOGGER.error("Error switching user in Iguana-IDM: '%s'", res.reason)
            return
        linked_reservations = await self.get_reservations(offset=offset, size=size)
        data = {
            "userId": self._access.mainUserId,
        }
        res = await self._access.api_call("switchuser", request=data)
        if res.status != 200:
            _LOGGER.error(
                "Error switching back to main user in Iguana-IDM: '%s'", res.reason
            )
        return linked_reservations
