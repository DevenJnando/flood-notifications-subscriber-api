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
from app.logging.log import get_logger


ATTEMPT_LIMIT = 5


def get_all_subscribers(session_maker: sessionmaker) -> list[Subscriber | None]:
    """
    Fetches all subscribers from the database.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :return: List of all subscribers
    """
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
            get_logger().error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def get_subscriber_by_id(session_maker: sessionmaker, subscriber_id: UUID) -> Subscriber | None:
    """
    Fetches a subscriber from the database by ID.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :param subscriber_id: Subscriber ID
    :return: Subscriber or None
    """

    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber | None = session.get(Subscriber, subscriber_id)
                if subscriber is None:
                    get_logger().error(HTTPStatus.NOT_FOUND)
                    get_logger().error(f"Bad Request: {subscriber_id} not found")
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                        detail=f"Subscriber with given id {subscriber_id} not found")
                return subscriber
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            get_logger().error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def get_subscriber_by_email(session_maker: sessionmaker, subscriber_email: str) -> Subscriber | None:
    """
    Fetches a subscriber from the database by email.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :param subscriber_email: Subscriber email
    :return: Subscriber or None
    """
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber | None = session.query(Subscriber).filter_by(email=subscriber_email).scalar()
                if subscriber is None:
                    get_logger().error(HTTPStatus.NOT_FOUND)
                    get_logger().error(f"Bad Request: {subscriber_email} not found")
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                        detail=f"Subscriber with given email {subscriber_email} not found")
                return subscriber
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            get_logger().error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def get_subscribers_by_postcode(session_maker: sessionmaker, postcode: str) -> list[Subscriber] | None:
    """
    Fetches a list of subscribers from the database by postcode.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :param postcode: Postcode
    :return: List of subscribers or None
    """
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
                get_logger().error(HTTPStatus.NOT_FOUND)
                get_logger().error(f"Bad Request: {postcode} not found")
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                    detail=f"No subscribers with postcode {postcode} found in database.")
            return subscribers_with_postcode
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            get_logger().error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def get_all_subscribers_by_postcodes(session_maker: sessionmaker, postcodes: set[str]) -> list[Subscriber | None]:
    """
    Fetches a list of subscribers from the database by a set of postcodes.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :param postcodes: Postcodes set
    :return: List of subscribers or None
    """
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
                get_logger().warning(f"No subscribers with postcodes {postcodes} found in database.")
            return subscribers_with_postcodes
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            get_logger().error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


async def add_postcodes_to_existing_subscriber(session_maker: sessionmaker, postcodes: list[str], email: str) -> None:
    """
    Adds postcodes to an existing subscriber.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :param postcodes: list of postcodes to be entered
    :param email: email address of the existing subscriber
    :return:
    """
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber = session.query(Subscriber).filter_by(email=email).scalar()
                print(subscriber)
                if subscriber is None:
                    get_logger().error(HTTPStatus.NOT_FOUND)
                    get_logger().error(f"Bad Request: {email} not found")
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                        detail=f"Failed to locate subscriber...")
                postcodes_to_add: list[Postcode] = list()
                for postcode in postcodes:
                    postcode = postcode.replace(" ", "")
                    exists = session.query(Postcode).filter_by(postcode=postcode, subscriber_id=subscriber.id).scalar() is not None
                    postcode_is_valid = await validate_postcode(postcode)
                    print("postcode is valid: ", postcode_is_valid)
                    print("exists in database: ", exists)
                    if not postcode_is_valid or exists:
                        get_logger().error(HTTPStatus.NO_CONTENT)
                        get_logger().error(f"Bad Request: {postcode} could not be found within its district.")
                        raise HTTPException(status_code=HTTPStatus.NO_CONTENT,
                                            detail=f"Postcode {postcode} not located in given district. \n"
                                                   f"(Hint: you may have entered the same postcode under this email twice!)")
                    postcode_object = Postcode(postcode=postcode)
                    postcode_object.subscriber = subscriber
                    postcodes_to_add.append(postcode_object)
                session.add_all(postcodes_to_add)
                session.commit()
                return
        except Exception as e:
            if type(e).__name__ == "HTTPException":
                raise e
            get_logger().error(f"Failed to access database. Retrying...\n"
                               f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                               f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


async def add_new_subscriber(session_maker: sessionmaker, subscriber_form: SubscriberForm) -> None:
    """
    Adds a new subscriber to the database.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :param subscriber_form: SubscriberForm object
    :return:
    :throws: HTTPException if form is invalid, if the postcode(s) aren't covered, or if the subscriber already exists
    """
    if len(subscriber_form.postcodes) > 10:
        get_logger().error(HTTPStatus.NOT_ACCEPTABLE)
        get_logger().error(f"Bad Request: {len(subscriber_form.postcodes)} postcodes were entered. "
                           f"Maximum number of postcodes is 10.")
        raise HTTPException(status_code=HTTPStatus.NOT_ACCEPTABLE,
                            detail=f"Bad Request: {len(subscriber_form.postcodes)} postcodes were entered. "
                            f"Maximum number of postcodes is 10.")

    attempt_number = 0
    try:
        subscriber_email: ValidatedEmail = validate_email(subscriber_form.email, check_deliverability=False)
    except EmailNotValidError:
        get_logger().error(HTTPStatus.NOT_ACCEPTABLE)
        get_logger().error(f"Bad Request: {subscriber_form.email} is invalid")
        raise HTTPException(status_code=HTTPStatus.NOT_ACCEPTABLE,
                            detail=f"The entered email {subscriber_form.email} is invalid")
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                normalized_email: str = subscriber_email.normalized
                exists: bool = session.query(Subscriber).filter_by(email=normalized_email).scalar() is not None
                if exists:
                    await add_postcodes_to_existing_subscriber(session_maker=session_maker,
                                                               postcodes=subscriber_form.postcodes,
                                                               email=normalized_email)
                    return
                subscriber = Subscriber(email=normalized_email)
                for postcode in subscriber_form.postcodes:
                    postcode = postcode.replace(" ", "")
                    postcode_is_valid = await validate_postcode(postcode)
                    if not postcode_is_valid:
                        get_logger().error(HTTPStatus.NO_CONTENT)
                        get_logger().error(f"Bad Request: {postcode} could not be found within its district.")
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
            get_logger().error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def delete_subscriber_by_id(session_maker: sessionmaker, subscriber_id: UUID) -> None:
    """
    Deletes a subscriber from the database by ID.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :param subscriber_id: Subscriber ID
    :return:
    :throws: HTTPException if subscriber does not exist
    """
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber | None = session.query(Subscriber).filter_by(id=subscriber_id).scalar()
                if subscriber is None:
                    get_logger().error(HTTPStatus.NOT_FOUND)
                    get_logger().error(f"Bad Request: {subscriber_id} not found")
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
            get_logger().error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")


def delete_subscriber_by_email(session_maker: sessionmaker, subscriber_email: str) -> None:
    """
    Deletes a subscriber from the database by Email.

    :param session_maker: SQLAlchemy sessionmaker factory object
    :param subscriber_email: Subscriber email
    :return:
    :throws: HTTPException if subscriber does not exist
    """
    attempt_number = 0
    while attempt_number < ATTEMPT_LIMIT:
        try:
            Session = scoped_session(session_maker)
            with Session() as session:
                subscriber: Subscriber | None = session.query(Subscriber).filter_by(email=subscriber_email).scalar()
                if subscriber is None:
                    get_logger().error(HTTPStatus.NOT_FOUND)
                    get_logger().error(f"Bad Request: {subscriber_email} not found")
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
            get_logger().error(f"Failed to access database. Retrying...\n"
                         f"(Attempt {attempt_number} of {ATTEMPT_LIMIT})\n"
                         f"{e}")
            attempt_number += 1
            time.sleep(5)
    get_logger().error(HTTPStatus.INTERNAL_SERVER_ERROR)
    get_logger().error("Attempt limit reached.")
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="Failed to retrieve subscribers from database...")

