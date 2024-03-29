import logging


def logging_config():
    """ Sets up the logging configuration. """

    log_format_str = "%(asctime)s [%(levelname)-8.8s]  %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_format_str)

    # Set log level for requests to data access api.
    logging.getLogger("request_handler").setLevel(logging.INFO)

    # Set log level for trade processes.
    logging.getLogger("trade_handler").setLevel(logging.DEBUG)

    # Set log level for requests to yahoo finance.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
