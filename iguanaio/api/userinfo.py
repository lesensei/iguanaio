import logging
from typing import Any, List
from urllib.parse import urljoin

from iguanaio.access import Access

_LOGGER = logging.getLogger(__package__)


class UserInfo:
    def __init__(self, access: Access):
        self._access = access

    async def get_user_info(self):
        """Get authenticated user information"""
        if not await self._access.is_authenticated():
            await self._access.authenticate()
        res = await self._access.api_call("summary")
        if res.status != 200:
            _LOGGER.error(
                "Error fetching Iguana-IDM user information: '%s'", res.reason
            )
            return
        return (await res.json(content_type="text/html"))["response"]

    async def get_personal_data(self):
        """Get personal data of authenticated user"""
        if not await self._access.is_authenticated():
            await self._access.authenticate()
        res = await self._access.api_call("personaldata")
        if res.status != 200:
            _LOGGER.error("Error fetching Iguana-IDM personal data: '%s'", res.reason)
            return
        return (await res.json(content_type="text/html"))["response"]

    async def get_linked_accounts(self):
        """Get accounts linked with authenticated user"""
        if not await self._access.is_authenticated():
            await self._access.authenticate()
        res = await self._access.api_call("linkedaccounts")
        if res.status != 200:
            _LOGGER.error(
                "Error fetching Iguana-IDM user information: '%s'", res.reason
            )
            return
        return (await res.json(content_type="text/html"))["response"]

    async def get_linked_user_info(self, users: List[str]):
        """Get linked account(s) info"""
        if not await self._access.is_authenticated():
            await self._access.authenticate()
        linked_info = {}
        for userId in users:
            data = {
                "userId": userId,
            }
            res = await self._access.api_call("switchuser", request=data)
            if res.status != 200:
                _LOGGER.error("Error switching user in Iguana-IDM: '%s'", res.reason)
                break
            linked_info[userId] = await self.get_user_info()
            data = {
                "userId": self._access.mainUserId,
            }
            res = await self._access.api_call("switchuser", request=data)
            if res.status != 200:
                _LOGGER.error(
                    "Error switching back to main user in Iguana-IDM: '%s'", res.reason
                )
                break
        return linked_info
