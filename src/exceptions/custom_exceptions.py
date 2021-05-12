class InvalidMarketIndexError(Exception):
    """ Exception raised for unrecognised market index label provided to the historical data manager."""
    def __init__(self, market_index_label):
        self.message = f"'{market_index_label}' is not a recognised market index label."
        super().__init__(self.message)


class InvalidHistoricalDataIndexError(Exception):
    """ Exception raised when a start date index value is a date that comes before the very first entry in a table."""
    def __init__(self, ticker, start_date_index, first_date_index_in_table):
        self.message = f"{start_date_index} comes before the very first date in the downloaded data " \
                       f"for {ticker} ({first_date_index_in_table})."
        super().__init__(self.message)


class InvalidHistoricalDataError(Exception):
    """ Exception raised when a start date index value is a date that comes before the very first entry in a table."""
    def __init__(self, ticker):
        self.message = f"'{ticker}' is marked as invalid, will not analyse."
        super().__init__(self.message)


class TradeCreationError(Exception):
    """ Exception raised when a trade cannot be created for a given reason."""
    def __init__(self, reason):
        self.message = f"Could not create trade: {reason}"
        super().__init__(self.message)


class TradeAnalysisError(Exception):
    """ Exception raised when no interesting stocks have been found in the analysis."""
    def __init__(self, date):
        self.message = f"No interesting tickers identified to be invested into"
        super().__init__(self.message)


class HistoricalDataValidationError(Exception):
    """ Exception raised when validator detects the given dataset is invalid. """
    def __init__(self, ticker, invalid_reason):
        self.message = f"'{ticker}' data invalid: {invalid_reason}"
        super().__init__(self.message)


class InvalidStrategyConfigException(Exception):
    """ Exception raised when a strategy configuration setting has is invalid/unrecognised. """
    def __init__(self, invalid_reason):
        self.message = f"Strategy configuration data invalid: {invalid_reason}"
        super().__init__(self.message)
