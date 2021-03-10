import pytest
import pandas as pd
from pytest_cases import parametrize, parametrize_with_cases
from src.data_validators import historical_data_validator
from os import listdir
import re


class DataCases:
    """ Grabs a list of all test case CSVs, then reads each one and prepares it to be used within the tests.
        A test case method is created for each test, extracting a valid and invalid case to be used by each one.
    """
    case_path = "data_validators/cases/historical_data_cases/"
    cases = listdir(case_path)
    case_ids = []

    # Set up dataframes to be used within historical_data_validator.
    for i, case_name in enumerate(cases):
        case = pd.read_csv(case_path + case_name)
        case['Date'] = pd.to_datetime(case['Date'])
        case = case.set_index("Date")
        pattern = re.compile("((valid|invalid).*).csv")
        match = pattern.match(case_name)
        case.id = match.group(1)
        case.valid = match.group(2)
        case_ids.append(match.group(1))
        case.ticker = "TEST"
        cases[i] = case

    @parametrize(case=case_ids)
    def case_test(self, case):
        """ Returns a row for each case to be used by the tests. """
        for case_df in self.cases:
            if case_df.id == case:
                return case_df


@pytest.mark.historical_data_validator
@parametrize_with_cases("case", cases=DataCases)
def test_data_validator(case):
    validator = historical_data_validator.HistoricalDataValidator(case, max_day_gap=5)
    expected = True if case.valid == "valid" else False
    result = validator.validate_data()

    assert result == expected
