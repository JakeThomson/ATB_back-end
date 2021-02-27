import logging as log
from exceptions.custom_exceptions import HistoricalDataValidationError


class HistoricalDataValidator:
    prev_row_values = None
    prev_row_date = None

    def __init__(self, dataframe, max_day_gap=5, percent_change_limit=100):
        self.dataframe = dataframe
        self.max_day_gap = max_day_gap
        self.percent_change_limit = percent_change_limit

    def date_gap_check(self, row_date):
        """ Checks the gap between the current iteration date, and the last read date. Save the date gap info to object
            attributes if it is higher than the currently recorded date gap.

        :param row_date: The date attached to the row being validated.
        :raises HistoricalDataValidationError: If data fails validation check.
        """

        day_gap = row_date - self.prev_row_date
        date_gap_str = f"{self.prev_row_date.date()} - {row_date.date()}"

        # Ignore date gap from when the 9/11 attacks forced the NYSE to close.
        if date_gap_str != "2001-09-10 - 2001-09-17":
            if day_gap.days > self.max_day_gap:
                invalid_reason = f"Date gap of {day_gap.days} days found ({date_gap_str})"
                raise HistoricalDataValidationError(self.dataframe.ticker, invalid_reason)

    def null_value_check(self, row_date, row_values):
        """ Checks the current row for null values.

        :param row_date: The date attached to the row being validated.
        :param row_values: The values contained in the row being validated.
        :raises HistoricalDataValidationError: If data fails validation check.
        """
        if row_values.isnull().values.any():
            invalid_reason = f"Missing values on date '{row_date}'"
            raise HistoricalDataValidationError(self.dataframe.ticker, invalid_reason)

    def repeated_values_check(self, row_date, row_values):
        """ Checks the current row for values that are repeated more than a set limit.

        :param row_date: The date attached to the row being validated.
        :param row_values: The values contained in the row being validated.
        :raises HistoricalDataValidationError: If data contains rows that are repeated more than the set limit.
        """
        repeat_limit = 7

        if self.prev_row_values.equals(row_values):
            # Slice of dataframe from the point the iterator is at.
            idx = self.dataframe.index.get_loc(row_date)
            temp_df = self.dataframe.iloc[idx:idx + repeat_limit]

            # Look to see if all rows in the dataframe slice are the same.
            rows_as_list = temp_df.T.values.tolist()
            for i, col in enumerate(rows_as_list):
                rows_as_list[i] = len(set(col))

            # If the length of the set is greater than 1, then the rows in the dataframe slice are not identical.
            if len(set(rows_as_list)) == 1:
                invalid_reason = f"Values repeated {repeat_limit} or more times ({row_date})"
                raise HistoricalDataValidationError(self.dataframe.ticker, invalid_reason)

    def unexplainable_value_change_check(self, row_date, row_values):
        """ Compares the current rows values against the previous, checking to see that there are no extreme changes

        :param row_values: The values contained in the row being validated.
        :raises HistoricalDataValidationError: If a value in the row has changed more than 100%.
        """

        value = row_values['close']
        prev_value = self.prev_row_values['close']

        percent_change = ((value - prev_value) / prev_value) * 100
        if abs(percent_change) > self.percent_change_limit:
            invalid_reason = f" Close value had a change of {round(percent_change,2)}% in one day ({row_date.date()})"
            raise HistoricalDataValidationError(self.dataframe.ticker, invalid_reason)

    def validate_data(self):
        """ Performs all validation checks on every row of the dataframe provided to the validator.

        :return: True if data is valid, False if invalid.
        """

        # Iterate through all rows and apply validation checks to each one.
        for row_date, row_values in self.dataframe.iterrows():
            try:
                # Checks that don't require comparison of previous row.
                self.null_value_check(row_date, row_values)

                # Don't apply checks that compare against previous row if there is no previous row.
                if self.prev_row_values is None or self.prev_row_date is None:
                    self.prev_row_values = row_values
                    self.prev_row_date = row_date
                    continue

                # Checks that compare against previous row.
                self.unexplainable_value_change_check(row_date, row_values)
                self.date_gap_check(row_date)
                self.repeated_values_check(row_date, row_values)

                # Comparison values needed
                self.prev_row_values = row_values
                self.prev_row_date = row_date

            # If a check throws an exception, log validation failure reason and return false.
            except HistoricalDataValidationError as invalidReason:
                log.warning(invalidReason)
                return False

        # Data passed all validation checks.
        return True
