import pytest
import pandas as pd
from pytest_cases import parametrize, parametrize_with_cases
from data_validators import historical_data_validator
from os import listdir
import re


class DataCases:
    """ Grabs a list of all test case CSVs, then reads each one and prepares it to be used within the tests.
        A test case method is created for each test, extracting a valid and invalid case to be used by each one.
    """
    case_path = "data_validators/cases/historical_data_cases/"
    cases = listdir(case_path)

    # Set up dataframes to be used within historical_data_validator.
    for i, case_name in enumerate(cases):
        case = pd.read_csv(case_path + case_name)
        case['Date'] = pd.to_datetime(case['Date'])
        case = case.set_index("Date")
        pattern = re.compile("(valid|invalid)_historical_data_(.*).csv")
        match = pattern.match(case_name)
        case.valid = match.group(1)
        case.label = match.group(2)
        case.ticker = "TEST"
        cases[i] = case

    # Extract invalid and valid cases relevant to the date_gap test.
    date_gap_cases = [case for case in cases if case.label == "date_gap" or case.valid == "valid"]

    @parametrize(case=("valid", "invalid"))
    def data_gap_select(self, case):
        """ Returns a row for each case to be used by the tests. """
        for dataframe in self.date_gap_cases:
            if dataframe.valid == case:
                return dataframe


@pytest.mark.historical_data_validator
@parametrize_with_cases("case", cases=DataCases, prefix="data_gap_")
def test_date_gap(case):
    validator = historical_data_validator.HistoricalDataValidator(case, max_day_gap=5)
    expected = True if case.valid == "valid" else False
    result = validator.validate_data()

    assert result == expected


