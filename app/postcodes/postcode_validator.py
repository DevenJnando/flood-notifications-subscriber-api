import re
from http import HTTPStatus
from typing import Any

from azure.core.async_paging import AsyncItemPaged
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
from fastapi import HTTPException

from app.connections import cosmosdb_client
from app.logging.log import get_logger


GET_POSTCODE_QUERY = ("SELECT * FROM c "
                      "where c.features[0].properties.mapit_code = @postcode "
                      "or c.features[0].properties.postcodes = @postcode")


async def async_check_postcode_is_notifiable(client: CosmosClient,
                                       postcode: str) -> bool:
    """
    Checks if a given postcode exists within the database. If it does, it is covered by this service, and
    therefore is notifiable. Otherwise it is not.

    :param client: CosmosDB client
    :param postcode: Postcode
    :return: True if postcode is notifiable, False otherwise
    """
    postcode = postcode.replace(" ", "")
    postcode_parameters = [dict(name="@postcode", value=postcode)]
    split_at: int = len(postcode) - 3
    district = postcode[:split_at]
    area_code = re.split(r'(^\D+)', district)[1:][0]
    postcode_container = cosmosdb_client.get_full_postcodes_container(client, area_code)
    try:
        postcodes: AsyncItemPaged[dict[str, Any]] = \
            postcode_container.query_items(query=GET_POSTCODE_QUERY,
                                           parameters=postcode_parameters,
                                           partition_key=district)
        async for postcode_object in postcodes:
            if (postcode_object['features'][0]['properties']['mapit_code'] == postcode
                or postcode_object['features'][0]['properties']['postcodes'] == postcode):
                return True
        return False
    except CosmosHttpResponseError as e:
        get_logger().error(f"Attempt to query postcode database failed: {e}")
        raise e


async def validate_postcode(postcode: str) -> bool:
    """
    Validates whether a given postcode is, or is not covered by the flood monitoring service.

    :param postcode: Postcode
    :return: True if postcode is valid, False otherwise
    """
    try:
        async with CosmosClient(cosmosdb_client.cosmos_endpoint, cosmosdb_client.credential) as client:
            postcode_is_valid = await async_check_postcode_is_notifiable(client, postcode)
            return postcode_is_valid
    except CosmosHttpResponseError as e:
        get_logger().error(f"Bad Request: {e}")
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Postcode {postcode} has no area, or districts associated with it.")