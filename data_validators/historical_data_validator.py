import logging as log
from exceptions.custom_exceptions import HistoricalDataValidationError

class HistoricalDataValidator:

    longest_date_gap = 0
    date_gap = ""
    prev_values = None
    prev_date = None
    valid = True

    def __init__(self, dataframe):
        self.dataframe = dataframe

    def date_gap_check(self, row_date):
        """ Checks the gap between the current iteration date, and the last read date. Save the date gap info to object
        attributes if it is higher than the currently recorded date gap.

        :param row_date:
        :return: none
        """
        day_gap = row_date - self.prev_date
        if day_gap.days > self.longest_date_gap:
            date_gap_str = f"{self.prev_date.date()} - {row_date.date()}"

            # Ignore date gap from when the 9/11 attacks forced the NYSE to close
            if date_gap_str != "2001-09-10 - 2001-09-17":
                self.date_gap = date_gap_str
                self.longest_date_gap = day_gap.days

            if day_gap.days > 5:
                invalid_reason = f"Date gap too high ({self.longest_date_gap} days ({self.date_gap}))"
                raise HistoricalDataValidationError(self.dataframe.ticker, invalid_reason)

    def empty_value_check(self, row_date, row_values):
        result = row_values.isnull()
        if row_values.isnull().values.any():
            invalid_reason = f"Missing values on date '{row_date}'"
            raise HistoricalDataValidationError(self.dataframe.ticker, invalid_reason)

    def validate_data(self):

        for row_date, row_values in self.dataframe.iterrows():
            try:
                self.empty_value_check(row_date, row_values)

                if self.prev_values is None or self.prev_date is None:
                    self.prev_values = row_values
                    self.prev_date = row_date
                    continue

                self.date_gap_check(row_date)
                self.prev_values = row_values
                self.prev_date = row_date

            except HistoricalDataValidationError as err:
                log.warning(err)
                return False

        return True

