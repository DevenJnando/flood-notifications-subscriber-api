import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from uuid import UUID, uuid4

from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker

from app.dbschema.schema import Subscriber, Postcode
from app.connections.database_orm import __get_az_mailing_list_engine, __get_sessionmaker
from app.services.subscriber_service import (get_all_subscribers,
                                             get_subscriber_by_id,
                                             get_subscriber_by_email,
                                             get_subscribers_by_postcode,
                                             add_new_subscriber,
                                             delete_subscriber_by_email, get_all_subscribers_by_postcodes,
                                             add_postcodes_to_existing_subscriber
                                             )
from app.models.pydantic_models.subscriber_form import SubscriberForm

from fastapi import HTTPException

mailing_list_engine = __get_az_mailing_list_engine()
session = __get_sessionmaker(mailing_list_engine)

def get_session() -> sessionmaker:
    return session


class SubscriberTests(IsolatedAsyncioTestCase):


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
        subscribers = get_all_subscribers(session_maker=session)
        assert len(subscribers) > 0


    def test_get_subscriber_by_id_exists(self):
        correct_id: UUID
        with session() as current_session:
            query = select("*").where(Subscriber.email == "petergriffin@test123.com")
            results = current_session.execute(query).all()
            correct_id = UUID(results[0][0])
        subscriber = get_subscriber_by_id(session_maker=session, subscriber_id=correct_id)
        assert subscriber.id == correct_id


    def test_get_subscriber_by_id_does_not_exist(self):
        non_existent_id: UUID = uuid4()
        self.assertRaises(HTTPException, lambda: get_subscriber_by_id(session_maker=session, subscriber_id=non_existent_id))


    def test_get_subscriber_by_email_exists(self):
        correct_email: str = ""
        with session() as current_session:
            query = select("*").where(Subscriber.email == "petergriffin@test123.com")
            results = current_session.execute(query).all()
            correct_email = results[0][1]
        subscriber = get_subscriber_by_email(session_maker=session, subscriber_email=correct_email)
        assert subscriber.email == correct_email


    def test_get_subscriber_by_email_does_not_exist(self):
        non_existent_email: str = "itwasmadeup@byawriter.com"
        self.assertRaises(HTTPException, lambda: get_subscriber_by_email(session_maker=session, subscriber_email=non_existent_email))


    def test_get_subscriber_by_postcode_exists(self):
        postcode = "G769DQ"
        list_of_subscribers: list[Subscriber] = get_subscribers_by_postcode(session_maker=session, postcode=postcode)
        assert len(list_of_subscribers) == 1 or len(list_of_subscribers) == 2
        subscriber: Subscriber = list_of_subscribers[0]
        assert subscriber.email == "petergriffin@test123.com" or subscriber.email == "newguy@newmail.com"


    def test_get_subscriber_by_postcode_does_not_exist(self):
        postcode = "DL91DY"
        self.assertRaises(HTTPException, lambda: get_subscribers_by_postcode(session_maker=session, postcode=postcode))


    def test_get_subscribers_by_postcodes_exists(self):
        postcodes: set[str] = {"G769DQ", "BT97FX"}
        list_of_subscribers: list[Subscriber] = get_all_subscribers_by_postcodes(session_maker=session, postcodes=postcodes)
        assert len(list_of_subscribers) > 0


    def test_get_subscriber_by_postcodes_do_not_exist(self):
        postcode: set[str] = {"DL91DY", "LAY8TF"}
        list_of_subscribers: list[Subscriber] = get_all_subscribers_by_postcodes(session_maker=session, postcodes=postcode)
        assert len(list_of_subscribers) == 0


    async def test_add_new_subscriber(self):
        email = "newguy@newmail.com"
        subscriber_form = SubscriberForm(email=email,
                                     postcodes=[
                                         "LA220DY"
                                     ])
        await add_new_subscriber(session_maker=session, subscriber_form=subscriber_form)
        new_subscriber = get_subscriber_by_email(session_maker=session, subscriber_email=email)
        assert new_subscriber.email == email


    async def test_add_existing_subscriber_new_postcodes(self):
        email = "petergriffin@test123.com"
        subscriber_form = SubscriberForm(email=email,
                                         postcodes=[
                                             "HU181QB",
                                             "TQ139AW"
                                         ])
        await add_postcodes_to_existing_subscriber(session_maker=session,
                                                   postcodes=subscriber_form.postcodes,
                                                   email=subscriber_form.email)
        with session() as ses:
            updated_subscriber = ses.query(Subscriber).filter_by(email=subscriber_form.email).scalar()
            updated_postcodes = ses.query(Postcode).filter_by(subscriber=updated_subscriber).all()
            contains_first_new_postcode: bool = False
            contains_second_new_postcode: bool = False
            for updated_postcode in updated_postcodes:
                if updated_postcode.postcode == "HU181QB":
                    contains_first_new_postcode = True
                if updated_postcode.postcode == "TQ139AW":
                    contains_second_new_postcode = True
            assert contains_first_new_postcode
            assert contains_second_new_postcode


    async def test_add_existing_subscriber_old_postcodes(self):
        email = "petergriffin@test123.com"
        subscriber_form = SubscriberForm(email=email,
                                         postcodes=[
                                             "G769DQ",
                                             "HU181QB"
                                         ])
        with self.assertRaises(HTTPException):
            await add_postcodes_to_existing_subscriber(session_maker=session,
                                                       postcodes=subscriber_form.postcodes,
                                                       email=subscriber_form.email)


    async def test_add_subscriber_non_valid_email(self):
        email = "<script> "\
                "console.log('doing naughty things') "\
                "</script>"

        subscriber_form = SubscriberForm(email=email,
                                         postcodes=[
                                             "BA17RZ",
                                             "B11QH"
                                         ])
        with self.assertRaises(HTTPException):
            await add_new_subscriber(session_maker=session, subscriber_form=subscriber_form)


    async def test_add_subscriber_non_valid_postcode(self):
        email = "postcode@notinrange.com"
        subscriber_form = SubscriberForm(email=email,
                                         postcodes=[
                                             "G769DQ",
                                             "BT97FX"
                                         ])
        with self.assertRaises(HTTPException):
            await add_new_subscriber(session_maker=session, subscriber_form=subscriber_form)


if __name__ == "__main__":
    unittest.main()
