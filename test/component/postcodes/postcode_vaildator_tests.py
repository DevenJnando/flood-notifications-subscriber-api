import unittest
from unittest import IsolatedAsyncioTestCase

from azure.cosmos.exceptions import CosmosHttpResponseError

from app.postcodes.postcode_validator import async_check_postcode_is_notifiable
from app.connections.cosmosdb_client import cosmos_endpoint, credential
from azure.cosmos.aio import CosmosClient

class PostcodeVaildatorTests(IsolatedAsyncioTestCase):


    async def test_validate_notifiable_four_digit_district_postcode_with_spaces(self):
        postcode = "LA22 0DY"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            is_notifiable = await async_check_postcode_is_notifiable(client, postcode)
            assert is_notifiable is True


    async def test_validate_notifiable_three_digit_district_postcode_with_spaces(self):
        postcode = "BA1 7RZ"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            is_notifiable = await async_check_postcode_is_notifiable(client, postcode)
            assert is_notifiable is True


    async def test_validate_notifiable_two_digit_district_postcode_with_spaces(self):
        postcode = "B1 1QH"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            is_notifiable = await async_check_postcode_is_notifiable(client, postcode)
            assert is_notifiable is True


    async def test_validate_non_notifiable_three_digit_district_postcode_with_spaces(self):
        postcode = "BT9 7FX"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            with self.assertRaises(CosmosHttpResponseError):
                await async_check_postcode_is_notifiable(client, postcode)


    async def test_validate_non_notifiable_two_digit_district_postcode_with_spaces(self):
        postcode = "X1 1QH"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            with self.assertRaises(CosmosHttpResponseError):
                await async_check_postcode_is_notifiable(client, postcode)


    async def test_validate_notifiable_four_digit_district_postcode_no_spaces(self):
        postcode = "LA22 0DY"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            is_notifiable = await async_check_postcode_is_notifiable(client, postcode)
            assert is_notifiable is True


    async def test_validate_notifiable_three_digit_district_postcode_no_spaces(self):
        postcode = "BA17RZ"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            is_notifiable = await async_check_postcode_is_notifiable(client, postcode)
            assert is_notifiable is True


    async def test_validate_notifiable_two_digit_district_postcode_no_spaces(self):
        postcode = "B11QH"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            is_notifiable = await async_check_postcode_is_notifiable(client, postcode)
            assert is_notifiable is True


    async def test_validate_non_notifiable_three_digit_district_postcode_no_spaces(self):
        postcode = "BT97FX"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            with self.assertRaises(CosmosHttpResponseError):
                await async_check_postcode_is_notifiable(client, postcode)


    async def test_validate_non_notifiable_two_digit_district_postcode_no_spaces(self):
        postcode = "X11QH"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            with self.assertRaises(CosmosHttpResponseError):
                await async_check_postcode_is_notifiable(client, postcode)


    async def test_process_garbage(self):
        postcode = "ALSDKFJALGKWRJWELKJSLFKSJFLK"
        async with CosmosClient(cosmos_endpoint, credential) as client:
            with self.assertRaises(CosmosHttpResponseError):
                await async_check_postcode_is_notifiable(client, postcode)



if __name__ == '__main__':
    unittest.main()