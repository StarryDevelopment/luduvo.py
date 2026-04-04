"""

This module contains functions and objects used internally to generate URLs.

"""

import logging

logger = logging.getLogger(__name__)

root_site = "luduvo.com"


class URLGenerator:
    """
    Generates URLs based on a chosen base URL.

    Attributes:
        base_url: The base URL.
    """

    def __init__(self, base_url: str):
        self.base_url: str = base_url

    def get_subdomain(self, subdomain: str, protocol: str = "https") -> str:
        """
        Returns the full URL of a subdomain, given the base subdomain name.

        Arguments:
            subdomain: The URL subdomain.
            protocol: The URL protocol.
        """
        full_url = f"{protocol}://{subdomain}.{self.base_url}"
        logger.debug("Generated subdomain URL: %s", full_url)
        return full_url

    def get_url(
        self,
        path: str,
        subdomain: str = "api",
        base_url: str = None,  # ty:ignore[invalid-parameter-default]
        protocol: str = "https",
    ) -> str:
        """
        Returns a full URL, given a subdomain name, protocol, and path.

        Arguments:
            path: The URL path.
            subdomain: The URL subdomain.
            base_url: The base URL.
            protocol: The URL protocol.
        """
        if base_url is None:
            base_url = self.base_url

        full_url = f"{protocol}://{subdomain}.{base_url}/{path}"
        logger.debug("Generated URL: %s", full_url)
        return full_url
