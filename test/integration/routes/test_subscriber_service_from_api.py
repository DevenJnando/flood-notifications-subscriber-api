import unittest
from http import HTTPStatus
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select, delete

from app.connections.database_orm import (__get_az_mailing_list_engine,
                                          __get_sessionmaker)
from app.main import app
from app.dbschema.schema import Subscriber, Postcode
from app.services.subscriber_service import delete_subscriber_by_email

client = TestClient(app)

mailing_list_engine = __get_az_mailing_list_engine()
session = __get_sessionmaker(mailing_list_engine)


class SubscriberTests(unittest.TestCase):


    @classmethod
    def tearDownClass(cls):
        delete_subscriber_by_email(session_maker=session, subscriber_email="newguy@newmail.com")
        with session() as current_session:
            statement1 = delete(Postcode).where(Postcode.postcode == "HU181QB",
                                                Postcode.subscriber_id == "903d1687-cde0-411e-b97a-3a497f14e528")
            statement2 = delete(Postcode).where(Postcode.postcode == "TQ139AW",
                                                Postcode.subscriber_id == "903d1687-cde0-411e-b97a-3a497f14e528")
            current_session.execute(statement1)
            current_session.execute(statement2)
            current_session.commit()


    def test_get_all_subscribers(self):
        response = client.get("/subscribers/all")
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) > 0


    def test_get_subscriber_by_id_exists(self):
        correct_id: str = ""
        with session() as current_session:
            query = select("*").where(Subscriber.email == "petergriffin@test123.com")
            results = current_session.execute(query).all()
            correct_id = str(UUID(results[0][0]))
        response = client.get("/subscribers/get/id/{}".format(correct_id))
        assert response.status_code == HTTPStatus.OK
        assert response.json().get("id") == correct_id


    def test_get_subscriber_by_id_does_not_exist(self):
        non_existent_id: str = str(uuid4())
        response = client.get("/subscribers/get/id/{}".format(non_existent_id))
        assert response.status_code == HTTPStatus.NOT_FOUND


    def test_get_subscriber_by_email_exists(self):
        correct_email: str = ""
        with session() as current_session:
            query = select("*").where(Subscriber.email == "petergriffin@test123.com")
            results = current_session.execute(query).all()
            print(results)
            correct_email = results[0][1]
        response = client.get("/subscribers/get/email/{}".format(correct_email))
        assert response.status_code == HTTPStatus.OK
        assert response.json().get("email") == correct_email


    def test_get_subscriber_by_email_does_not_exist(self):
        non_existent_email: str = "itwasmadeup@byawriter.com"
        response = client.get("/subscribers/get/email/{}".format(non_existent_email))
        assert response.status_code == HTTPStatus.NOT_FOUND


    def test_add_new_subscriber(self):
        response = client.post("/subscribers/add",
                               data={"email": "newguy@newmail.com",
                                     "postcodes": [
                                         "LA220DY"
                                     ]})
        assert response.status_code == HTTPStatus.CREATED


    def test_add_existing_subscriber_with_new_postcodes(self):
        response = client.post("/subscribers/add",
                               data={"email": "petergriffin@test123.com",
                                     "postcodes": [
                                         "HU181QB",
                                         "TQ139AW"
                                     ]})
        assert response.status_code == HTTPStatus.CREATED


    def test_add_existing_subscriber_with_old_postcodes(self):
        response = client.post("/subscribers/add",
                               data={"email": "petergriffin@test123.com",
                                     "postcodes": [
                                         "HU181QB",
                                         "TQ139AW"
                                     ]})
        assert response.status_code == HTTPStatus.NO_CONTENT


    def test_add_subscriber_non_valid_email(self):
        response = client.post("/subscribers/add",
                               data={"email": "<script> "
                                              "console.log('doing naughty things') "
                                              "</script>",
                                     "postcodes": [
                                         "G769DQ",
                                         "BT97FX"
                                     ]
                                     }
                               )
        assert response.status_code == HTTPStatus.NOT_ACCEPTABLE


    def test_add_subscriber_non_valid_postcode_area(self):
        response = client.post("/subscribers/add",
                               data={"email": "postcode@notinrange.com",
                                     "postcodes": [
                                         "G769DQ",
                                         "BT97FX"
                                     ]
                                     }
                               )
        assert response.status_code == HTTPStatus.NOT_FOUND


    def test_add_subscriber_non_valid_postcode(self):
        response = client.post("/subscribers/add",
                               data={"email": "postcode@notinrange.com",
                                     "postcodes": [
                                         "BA1III",
                                         "B1III"
                                     ]
                                     }
                               )
        assert response.status_code == HTTPStatus.NO_CONTENT


if __name__ == "__main__":
    unittest.main()
