
""" This file is simply to save the hassle of typing the target URL and error handling in every HTTP request sent to
    the data access API throughout the application. """

import requests
import logging

logger = logging.getLogger("requests")
URL = None


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
    try:
        response = requests.put(URL + endpoint, data=data)
    except Exception as e:
        logger.error(f"Error occurred when sending PUT request to {URL}{endpoint}")
        raise e

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
    try:
        response = requests.patch(URL + endpoint, data=data)
    except ConnectionError as e:
        logger.error(f"Error occurred when sending PATCH request to {URL}{endpoint}")
        raise e

    if response.status_code >= 400:
        logger.error(f"Status code {response.status_code} received when sending PATCH request to {URL}{endpoint}")

    return response
