from os import getenv
from dotenv import load_dotenv

try:
    load_dotenv()
    cosmos_endpoint = getenv("POSTCODES_GEOJSON_COSMOSDB_ENDPOINT")
    postcode_database_suffix = getenv("POSTCODE_DATABASE_SUFFIX")
    full_postcode_container_suffix = getenv("POSTCODE_FULL_CONTAINER_SUFFIX")
except KeyError:
    cosmos_endpoint = "DefaultAzureCredential"
    postcode_database_suffix = "POSTCODE_DATABASE_SUFFIX"
    full_postcode_container_suffix = "POSTCODE_FULL_CONTAINER_SUFFIX"