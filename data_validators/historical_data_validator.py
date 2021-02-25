import logging as log


class HistoricalDataValidator:

    longest_date_gap = 0
    date_gap = ""
    prev_values = None
    prev_date = None
    invalid_reason = ""

    def __init__(self, dataframe):
        self.dataframe = dataframe

    def date_gap_check(self, date):
        """ Checks the gap between the current iteration date, and the last read date. Save the date gap info to object
        attributes if it is higher than the currently recorded date gap.

        :param date:
        :return: none
        """
        day_gap = date - self.prev_date
        if day_gap.days > self.longest_date_gap:
            date_gap_str = f"{self.prev_date.date()} - {date.date()}"

            # Ignore date gap from when the 9/11 attacks forced the NYSE to close
            if date_gap_str != "2001-09-10 - 2001-09-17":
                self.date_gap = date_gap_str
                self.longest_date_gap = day_gap.days

    def validate_data(self):

        valid = True

        for date, values in self.dataframe.iterrows():
            if self.prev_values is None or self.prev_date is None:
                self.prev_values = values
                self.prev_date = date
                continue

            self.date_gap_check(date)
            self.prev_values = values
            self.prev_date = date

        if self.longest_date_gap > 5:
            invalid_reason = f"Date gap too high ({self.longest_date_gap} days ({self.date_gap}))"
            log.warning(f"{self.dataframe.ticker} data is invalid: {invalid_reason}")
            valid = False

        return valid

