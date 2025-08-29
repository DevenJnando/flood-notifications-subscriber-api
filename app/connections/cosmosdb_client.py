from app.env_vars import *
from azure.common import AzureMissingResourceHttpError
from azure.cosmos.container import ContainerProxy
from azure.cosmos.aio import CosmosClient
from azure.identity import DefaultAzureCredential

from app.logging.log import get_logger

credential: DefaultAzureCredential = DefaultAzureCredential()


def get_full_postcodes_container(client: CosmosClient, area_code: str) -> ContainerProxy:
    """
    Gets the full postcode container by using the area code as a reference.

    @param client: Cosmos DB client
    @param area_code: Area code - a hardcoded database and container suffix are attached to this parameter
    @return ContainerProxy: this is the container object which is used to make queries to.
    @throws AzureMissingResourceHttpError: - If no container, or postcode database exists, this error is thrown.
    """
    try:
        return (client
                .get_database_client(area_code + postcode_database_suffix)
                .get_container_client(area_code + full_postcode_container_suffix)
                )
    except AzureMissingResourceHttpError as e:
        get_logger().fatal("Postcode Database/Container not present in cosmos environment.")
        get_logger().fatal(e)
        raise e