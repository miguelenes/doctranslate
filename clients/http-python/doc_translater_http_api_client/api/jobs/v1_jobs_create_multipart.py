from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_error_envelope import ApiErrorEnvelope
from ...models.body_v1_jobs_create_multipart import BodyV1JobsCreateMultipart
from ...models.http_validation_error import HTTPValidationError
from ...models.job_create_response import JobCreateResponse
from ...types import Response


def _get_kwargs(
    *,
    body: BodyV1JobsCreateMultipart,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/jobs",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorEnvelope | HTTPValidationError | JobCreateResponse | None:
    if response.status_code == 202:
        response_202 = JobCreateResponse.from_dict(response.json())

        return response_202

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
) -> Response[ApiErrorEnvelope | HTTPValidationError | JobCreateResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: BodyV1JobsCreateMultipart,
) -> Response[ApiErrorEnvelope | HTTPValidationError | JobCreateResponse]:
    """Create Job

    Args:
        body (BodyV1JobsCreateMultipart):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorEnvelope | HTTPValidationError | JobCreateResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: BodyV1JobsCreateMultipart,
) -> ApiErrorEnvelope | HTTPValidationError | JobCreateResponse | None:
    """Create Job

    Args:
        body (BodyV1JobsCreateMultipart):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorEnvelope | HTTPValidationError | JobCreateResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: BodyV1JobsCreateMultipart,
) -> Response[ApiErrorEnvelope | HTTPValidationError | JobCreateResponse]:
    """Create Job

    Args:
        body (BodyV1JobsCreateMultipart):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorEnvelope | HTTPValidationError | JobCreateResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: BodyV1JobsCreateMultipart,
) -> ApiErrorEnvelope | HTTPValidationError | JobCreateResponse | None:
    """Create Job

    Args:
        body (BodyV1JobsCreateMultipart):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorEnvelope | HTTPValidationError | JobCreateResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
