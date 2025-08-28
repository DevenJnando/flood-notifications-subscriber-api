import logging
import time
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from email_validator import validate_email, EmailNotValidError, ValidatedEmail
from sqlalchemy.orm.scoping import scoped_session

from app.dbschema.schema import Subscriber, Postcode
from app.models.pydantic_models.subscriber_form import SubscriberForm
from app.postcodes.postcode_validator import validate_postcode


ATTEMPT_LIMIT = 5

logger = logging.getLogger(__name__)


def get_all_subscribers(session_maker: sessionmaker) -> list[Subscriber | None]:
    subscribers: list[Subscriber] = []
    subscriber_objects: list[Subscriber] = []
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                query = select(Subscriber.id, Subscriber.email)
                subscribers = session.execute(query).all()
            for subscriber in subscribers:
                subscriber_object = Subscriber(id=subscriber.id, email=subscriber.email)
                subscriber_objects.append(subscriber_object)
            return subscriber_objects
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            logger.error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def get_subscriber_by_id(session_maker: sessionmaker, subscriber_id: UUID) -> Subscriber | None:
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber | None = session.get(Subscriber, subscriber_id)
                if subscriber is None:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                        detail=f"Subscriber with given id {subscriber_id} not found")
                return subscriber
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            logger.error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def get_subscriber_by_email(session_maker: sessionmaker, subscriber_email: str) -> Subscriber | None:
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber | None = session.query(Subscriber).filter_by(email=subscriber_email).scalar()
                if subscriber is None:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                        detail=f"Subscriber with given email {subscriber_email} not found")
                return subscriber
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            logger.error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def get_subscribers_by_postcode(session_maker: sessionmaker, postcode: str) -> list[Subscriber] | None:
    subscribers_with_postcode: list[Subscriber] = []
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                statement = (select(Subscriber, Postcode)
                             .join(Subscriber.postcodes)
                             .order_by(Subscriber.id, Postcode.id)
                             .where(Postcode.postcode == postcode))
                for result in session.execute(statement):
                    subscribers_with_postcode.append(result.Subscriber)
            if len(subscribers_with_postcode) == 0:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                    detail=f"No subscribers with postcode {postcode} found in database.")
            return subscribers_with_postcode
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            logger.error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def get_all_subscribers_by_postcodes(session_maker: sessionmaker, postcodes: set[str]) -> list[Subscriber | None]:
    subscribers_with_postcodes: list[Subscriber] = []
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                statement = (select(Subscriber, Postcode)
                             .join(Subscriber.postcodes)
                             .order_by(Subscriber.id, Postcode.id)
                             .where(Postcode.postcode.in_(postcodes)))
                for result in session.execute(statement):
                    subscribers_with_postcodes.append(result.Subscriber)
            if len(subscribers_with_postcodes) == 0:
                logger.warning(f"No subscribers with postcodes {postcodes} found in database.")
            return subscribers_with_postcodes
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            logger.error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


async def add_new_subscriber(session_maker: sessionmaker, subscriber_form: SubscriberForm) -> None:
    attempt_number = 0
    try:
        subscriber_email: ValidatedEmail = validate_email(subscriber_form.email, check_deliverability=False)
    except EmailNotValidError:
        raise HTTPException(status_code=HTTPStatus.NOT_ACCEPTABLE,
                            detail=f"The entered email {subscriber_form.email} is invalid")
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                normalized_email: str = subscriber_email.normalized
                exists: bool = session.query(Subscriber).filter_by(email=normalized_email).scalar() is not None
                print(exists)
                if exists:
                    raise HTTPException(status_code=HTTPStatus.CONFLICT,
                                        detail=f"Subscriber with given email {subscriber_email} already exists")
                subscriber = Subscriber(email=normalized_email)
                for postcode in subscriber_form.postcodes:
                    postcode = postcode.replace(" ", "")
                    postcode_is_valid = await validate_postcode(postcode)
                    if not postcode_is_valid:
                        raise HTTPException(status_code=HTTPStatus.NO_CONTENT,
                                            detail=f"Postcode {postcode} not located in given district.")
                    postcode_object = Postcode(postcode=postcode)
                    subscriber.postcodes.append(postcode_object)
                session.add(subscriber)
                session.commit()
                return
        except Exception as e:
            print(e)
            if type(e).__name__ == "HTTPException":
                raise e
            logger.error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def delete_subscriber_by_id(session_maker: sessionmaker, subscriber_id: UUID) -> None:
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber | None = session.query(Subscriber).filter_by(id=subscriber_id).scalar()
                if subscriber is None:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                        detail=f"Could not delete subscriber with id '{subscriber_id}' "
                                               f"because no such subscriber exists in the database.")
                statement = (select(Subscriber, Postcode)
                             .join(Subscriber.postcodes)
                             .order_by(Subscriber.id, Postcode.id)
                             .where(Subscriber.id == subscriber_id))
                for result in session.execute(statement):
                    session.delete(result.Postcode)
                session.delete(subscriber)
                session.commit()
                return
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            logger.error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def delete_subscriber_by_email(session_maker: sessionmaker, subscriber_email: str) -> None:
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber | None = session.query(Subscriber).filter_by(email=subscriber_email).scalar()
                if subscriber is None:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                        detail=f"Could not delete subscriber with email '{subscriber_email}' "
                                               f"because no such subscriber exists in the database.")
                statement = (select(Subscriber, Postcode)
                             .join(Subscriber.postcodes)
                             .order_by(Subscriber.id, Postcode.id)
                             .where(Subscriber.id == subscriber.id))
                for result in session.execute(statement):
                    session.delete(result.Postcode)
                session.delete(subscriber)
                session.commit()
                return
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            logger.error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    logger.error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")

