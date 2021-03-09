
""" This file is simply to save the hassle of typing the target URL and error handling in every HTTP request sent to
    the data access API throughout the application. """

import requests
import logging
import time

logger = logging.getLogger("requests")
URL = None
max_attempts = 5
retry_delay_seconds = 3


def set_environment(environment):
    global URL
    if environment.lower() == "prod":
        URL = "https://trading-api.jake-t.codes"
    elif environment.lower() == "local":
        URL = "http://127.0.0.1:8080"
    logger.info(f"Connecting to data access API on {URL}")


def put(endpoint, data):
    """ Sends a PUT request to the specified endpoint.

    :param endpoint: The endpoint to send the request to.
    :param data: The data to be placed in the body of the request.
    :return response: The response object.
    """
    logger.debug(f"Sending PUT request to '{URL}{endpoint}' with payload: {data}")
    attempts = 0
    while True:
        attempts += 1
        try:
            response = requests.put(URL + endpoint, data=data)
            break
        except requests.exceptions.ConnectionError as e:
            # Handle connection errors.
            if attempts < max_attempts:
                logger.warning(f"Could not connect to {URL}, retrying in {retry_delay_seconds} seconds...")
                time.sleep(3)
                continue
            else:
                logger.critical(f"Could not connect to {URL} after {attempts} attempts to send PUT request to {endpoint}.")
                exit()

    if attempts > 1:
        logger.info(f"Successfully sent PUT request to {URL}{endpoint} after {attempts} attempts")

    if response.status_code >= 400:
        logger.error(f"Status code {response.status_code} received when sending PUT request to {URL}{endpoint}")

    return response


def patch(endpoint, data):
    """ Sends a PATCH request to the specified endpoint.

    :param endpoint: The endpoint to send the request to.
    :param data: The data to be placed in the body of the request.
    :return response: The response object.
    """
    logger.debug(f"Sending PATCH request to '{URL}{endpoint}' with payload: {str(data)}")
    attempts = 0
    while True:
        attempts += 1
        try:
            response = requests.patch(URL + endpoint, data=data)
            break
        except requests.exceptions.ConnectionError as e:
            # Handle connection errors.
            if attempts < max_attempts:
                logger.warning(f"Could not connect to {URL}, retrying in {retry_delay_seconds} seconds...")
                time.sleep(3)
                continue
            else:
                logger.critical(f"Could not connect to {URL} after {attempts} attempts to "
                                f"send PATCH request to {endpoint}.")
                exit()

    if attempts > 1:
        logger.info(f"Successfully sent PUT request to {URL}{endpoint} after {attempts} attempts")

    if response.status_code >= 400:
        logger.error(f"Status code {response.status_code} received when sending PATCH request to {URL}{endpoint}")

    return response


def post(endpoint, data):
    """ Sends a PATCH request to the specified endpoint.

    :param endpoint: The endpoint to send the request to.
    :param data: The data to be placed in the body of the request.
    :return response: The response object.
    """
    logger.debug(f"Sending POST request to '{URL}{endpoint}' with payload: {str(data)}")
    attempts = 0
    while True:
        attempts += 1
        try:
            print(data)
            response = requests.post(URL + endpoint, json=data)
            break
        except requests.exceptions.ConnectionError as e:
            # Handle connection errors.
            if attempts < max_attempts:
                logger.warning(f"Could not connect to {URL}, retrying in {retry_delay_seconds} seconds...")
                time.sleep(3)
                continue
            else:
                logger.critical(f"Could not connect to {URL} after {attempts} attempts to "
                                f"send POST request to {endpoint}.")
                exit()

    if attempts > 1:
        logger.info(f"Successfully sent POST request to {URL}{endpoint} after {attempts} attempts")

    if response.status_code >= 400:
        logger.error(f"Status code {response.status_code} received when sending POST request to {URL}{endpoint}")

    return response
