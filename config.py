import logging


def logging_config():
    """ Sets up the logging configuration. """

    log_format_str = "%(asctime)s [%(levelname)-7.7s]  %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_format_str)

    # Set log level for requests to data access api.
    logging.getLogger("requests").setLevel(logging.INFO)

    # Set log level for requests to yahoo finance.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
