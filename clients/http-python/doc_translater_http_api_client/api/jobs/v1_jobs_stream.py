from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_error_envelope import ApiErrorEnvelope
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    job_id: str,
    *,
    full_events: bool | Unset = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["full_events"] = full_events

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/jobs/{job_id}/stream".format(
            job_id=quote(str(job_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ApiErrorEnvelope | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = cast(Any, None)
        return response_200

    if response.status_code == 401:
        response_401 = ApiErrorEnvelope.from_dict(response.json())

        return response_401

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | ApiErrorEnvelope | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient,
    full_events: bool | Unset = False,
) -> Response[Any | ApiErrorEnvelope | HTTPValidationError]:
    """Stream Job Progress

    Args:
        job_id (str):
        full_events (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ApiErrorEnvelope | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        full_events=full_events,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    job_id: str,
    *,
    client: AuthenticatedClient,
    full_events: bool | Unset = False,
) -> Any | ApiErrorEnvelope | HTTPValidationError | None:
    """Stream Job Progress

    Args:
        job_id (str):
        full_events (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ApiErrorEnvelope | HTTPValidationError
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
        full_events=full_events,
    ).parsed


async def asyncio_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient,
    full_events: bool | Unset = False,
) -> Response[Any | ApiErrorEnvelope | HTTPValidationError]:
    """Stream Job Progress

    Args:
        job_id (str):
        full_events (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ApiErrorEnvelope | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        full_events=full_events,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: str,
    *,
    client: AuthenticatedClient,
    full_events: bool | Unset = False,
) -> Any | ApiErrorEnvelope | HTTPValidationError | None:
    """Stream Job Progress

    Args:
        job_id (str):
        full_events (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ApiErrorEnvelope | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            full_events=full_events,
        )
    ).parsed
