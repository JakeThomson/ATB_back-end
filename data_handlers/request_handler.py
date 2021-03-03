
"""This file is simply to save the hassle of typing the target URL and error handling in every HTTP request
throughout the application. """

import requests
URL = "https://trading-api.jake-t.codes"


def put(endpoint, data):
    """ Sends a PUT request to the specified endpoint.

    :param endpoint: The endpoint to send the request to.
    :param data: The data to be placed in the body of the request.
    :return response: The response object.
    """
    response = requests.put(URL + endpoint, data=data)
    return response
