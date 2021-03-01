class InvalidMarketIndexError(Exception):
    """ Exception raised for unrecognised market index label provided to the historical data manager."""

    def __init__(self, market_index_label):
        self.message = f"'{market_index_label}' is not a recognised market index label."
        super().__init__(self.message)


class HistoricalDataValidationError(Exception):
    """ Exception raised when validator detects the given dataset is invalid. """

    def __init__(self, ticker, invalid_reason):
        self.message = f"'{ticker}' data invalid: {invalid_reason}"
        super().__init__(self.message)
