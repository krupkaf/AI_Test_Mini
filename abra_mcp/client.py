"""HTTP client for Abra Gen API communication."""

import logging
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from .config import AbraConfig

logger = logging.getLogger(__name__)


class AbraAPIError(Exception):
    """Base exception for Abra API errors."""

    pass


class AbraAuthenticationError(AbraAPIError):
    """Authentication failed."""

    pass


class AbraNotFoundError(AbraAPIError):
    """Resource not found (404)."""

    pass


class AbraValidationError(AbraAPIError):
    """Validation error (400)."""

    pass


class AbraClient:
    """HTTP client for Abra Gen API.

    Handles:
    - HTTP Basic Authentication
    - Request/response formatting
    - Error handling and retries
    - URL construction according to Abra API format
    """

    def __init__(self, config: AbraConfig) -> None:
        """Initialize Abra API client.

        Args:
            config: Abra configuration with connection details
        """
        self.config = config
        self.client = httpx.AsyncClient(
            auth=httpx.BasicAuth(config.username, config.password),
            timeout=config.timeout,
            follow_redirects=True,
        )
        logger.info(f"Initialized AbraClient for {config.base_url}")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        logger.debug("Closed AbraClient")

    def _construct_url(
        self,
        collection: str,
        resource_id: Optional[str] = None,
        subcollection: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> str:
        """Construct URL according to Abra API format.

        Args:
            collection: Business object collection name (e.g., "issuedinvoices")
            resource_id: Optional resource ID
            subcollection: Optional subcollection name
            params: Optional query parameters

        Returns:
            Complete URL for the request
        """
        url_parts = [self.config.base_url, collection]

        if resource_id:
            url_parts.append(resource_id)

        if subcollection:
            url_parts.append(subcollection)

        url = "/".join(url_parts)

        if params:
            # Filter out None values and convert to strings
            clean_params = {k: str(v) for k, v in params.items() if v is not None}
            if clean_params:
                url += "?" + urlencode(clean_params)

        return url

    async def _request(
        self,
        method: str,
        url: str,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL for the request
            json: Optional JSON body for POST/PUT requests

        Returns:
            Response data as dictionary or list

        Raises:
            AbraAuthenticationError: If authentication fails (401, 403)
            AbraNotFoundError: If resource not found (404)
            AbraValidationError: If validation fails (400)
            AbraAPIError: For other API errors
        """
        logger.debug(f"{method} {url}")

        try:
            response = await self.client.request(method, url, json=json)

            # Handle authentication errors
            if response.status_code in (401, 403):
                raise AbraAuthenticationError(
                    f"Authentication failed: {response.status_code} {response.text}"
                )

            # Handle not found
            if response.status_code == 404:
                raise AbraNotFoundError(f"Resource not found: {url}")

            # Handle validation errors
            if response.status_code == 400:
                raise AbraValidationError(f"Validation error: {response.text}")

            # Raise for other HTTP errors
            response.raise_for_status()

            # Return JSON response
            if response.text:
                return response.json()
            return {}

        except httpx.TimeoutException as e:
            raise AbraAPIError(f"Request timeout: {e}")
        except httpx.NetworkError as e:
            raise AbraAPIError(f"Network error: {e}")
        except httpx.HTTPStatusError as e:
            raise AbraAPIError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise AbraAPIError(f"Unexpected error: {e}")

    async def get(
        self,
        collection: str,
        resource_id: Optional[str] = None,
        subcollection: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """GET request to Abra API.

        Args:
            collection: Business object collection name
            resource_id: Optional resource ID for specific object
            subcollection: Optional subcollection name
            params: Optional query parameters (select, where, orderby, etc.)

        Returns:
            Response data

        Examples:
            # Get all invoices
            await client.get("issuedinvoices")

            # Get specific invoice
            await client.get("issuedinvoices", resource_id="1400000101")

            # Get invoices with filters
            await client.get(
                "issuedinvoices",
                params={"select": "ID,Amount", "where": "Amount gt 10000"}
            )
        """
        url = self._construct_url(collection, resource_id, subcollection, params)
        return await self._request("GET", url)

    async def post(
        self,
        collection: str,
        data: dict[str, Any],
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """POST request to Abra API (create new resource).

        Args:
            collection: Business object collection name
            data: Data for the new resource
            params: Optional query parameters

        Returns:
            Created resource data
        """
        url = self._construct_url(collection, params=params)
        return await self._request("POST", url, json=data)  # type: ignore

    async def put(
        self,
        collection: str,
        resource_id: str,
        data: dict[str, Any],
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """PUT request to Abra API (update resource).

        Args:
            collection: Business object collection name
            resource_id: Resource ID to update
            data: Updated data
            params: Optional query parameters

        Returns:
            Updated resource data
        """
        url = self._construct_url(collection, resource_id, params=params)
        return await self._request("PUT", url, json=data)  # type: ignore

    async def delete(
        self,
        collection: str,
        resource_id: str,
    ) -> dict[str, Any]:
        """DELETE request to Abra API.

        Args:
            collection: Business object collection name
            resource_id: Resource ID to delete

        Returns:
            Response data
        """
        url = self._construct_url(collection, resource_id)
        return await self._request("DELETE", url)  # type: ignore

    async def query(
        self,
        collection: str,
        select: Optional[str] = None,
        where: Optional[str] = None,
        orderby: Optional[str] = None,
        expand: Optional[str] = None,
        skip: Optional[int] = None,
        take: Optional[int] = None,
        groupby: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Execute a query on a collection with various parameters.

        This is a convenience method that constructs query parameters
        according to Abra API query language.

        Args:
            collection: Business object collection name
            select: Fields to return (e.g., "ID,Name,Amount")
            where: Filter condition (e.g., "Amount gt 10000")
            orderby: Sorting (e.g., "Amount desc")
            expand: Include related objects (e.g., "Firm_ID")
            skip: Number of records to skip (pagination)
            take: Number of records to return (pagination)
            groupby: Grouping field (e.g., "Firm_ID")

        Returns:
            List of matching records

        Examples:
            # Get all firms with name and code
            await client.query("firms", select="ID,Code,Name")

            # Get invoices over 10000, sorted by amount
            await client.query(
                "issuedinvoices",
                select="ID,Amount,Firm_ID.Name",
                where="Amount gt 10000",
                orderby="Amount desc",
                expand="Firm_ID"
            )

            # Paginated results
            await client.query("storecards", select="ID,Code,Name", skip=0, take=10)
        """
        params: dict[str, Any] = {}

        if select:
            params["select"] = select
        if where:
            params["where"] = where
        if orderby:
            params["orderby"] = orderby
        if expand:
            params["expand"] = expand
        if skip is not None:
            params["skip"] = skip
        if take is not None:
            params["take"] = take
        if groupby:
            params["groupby"] = groupby

        result = await self.get(collection, params=params)

        # Ensure we always return a list
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            # Single object returned, wrap in list
            return [result]
        return []
