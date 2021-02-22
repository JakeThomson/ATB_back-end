class InvalidMarketIndexError(Exception):
    """Exception raised for unrecognised market index label provided to the historical data manager."""

    def __init__(self, source_label):
        self.message = f"'{source_label}' is not a recognised data source label."
        super().__init__(self.message)
