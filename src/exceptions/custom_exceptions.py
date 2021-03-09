class InvalidMarketIndexError(Exception):
    """ Exception raised for unrecognised market index label provided to the historical data manager."""

    def __init__(self, market_index_label):
        self.message = f"'{market_index_label}' is not a recognised market index label."
        super().__init__(self.message)


class InvalidHistoricalDataIndexError(Exception):
    """ Exception raised when a start date index value is a date that comes before the very first entry in a CSV."""

    def __init__(self, ticker, start_date_index, first_date_index_in_csv):
        self.message = f"{start_date_index} comes before the very first date in the downloaded data " \
                       f"for {ticker} ({first_date_index_in_csv})."
        super().__init__(self.message)


class TradeCreationError(Exception):
    """ Exception raised when a start date index value is a date that comes before the very first entry in a CSV."""

    def __init__(self, reason):
        self.message = f"Could not create trade: {reason}"
        super().__init__(self.message)

class HistoricalDataValidationError(Exception):
    """ Exception raised when validator detects the given dataset is invalid. """

    def __init__(self, ticker, invalid_reason):
        self.message = f"'{ticker}' data invalid: {invalid_reason}"
        super().__init__(self.message)
