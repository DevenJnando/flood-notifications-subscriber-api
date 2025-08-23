from app.env_vars import *
from azure.common import AzureMissingResourceHttpError
from azure.cosmos.container import ContainerProxy
from azure.cosmos.aio import CosmosClient
from azure.identity import DefaultAzureCredential


credential: DefaultAzureCredential = DefaultAzureCredential()


def get_full_postcodes_container(client: CosmosClient, area_code: str) -> ContainerProxy:
    try:
        return (client
                .get_database_client(area_code + postcode_database_suffix)
                .get_container_client(area_code + full_postcode_container_suffix)
                )
    except AzureMissingResourceHttpError as e:
        raise e