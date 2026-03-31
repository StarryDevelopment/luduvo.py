from .utils import setup_logger
from .utilities.classes import User
from .utilities.exceptions import BadRequest, NotFound, UserNotFound
from .utilities.url import URLGenerator
from .utilities.requests import Requests


logger = setup_logger()


class Client:
    def __init__(self, base_url="luduvo.com"):
        self._url_generator: URLGenerator = URLGenerator(base_url=base_url)
        self._requests: Requests = Requests()

        self.url_generator: URLGenerator = self._url_generator
        self.requests: Requests = self._requests

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    # --------------------------
    # API Endpoints
    # --------------------------

    async def get_user(self, user_id: int) -> User:
        """
        Gets a user with the specified user ID.

        Arguments:
            user_id: A Roblox user ID.

        Returns:
            A user object.
        """
        try:
            user_response = await self._requests.get(
                url=self.url_generator.get_url("api", f"users/{user_id}/profile")
            )
        except NotFound as exception:
            raise UserNotFound(
                message="Invalid user.", response=exception.response
            ) from None
        user_data = user_response.json()
        return User(client=self, data=user_data)
