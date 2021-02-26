import pytest
import pandas as pd
from pytest_cases import parametrize, parametrize_with_cases
from data_validators import date_validator


class DateCases:
    """ Loads up the cases from the CSV and provides each row as a test case for each test. """

    cases = pd.read_csv('data_validators/cases/date_validator_cases.csv')
    cases['date'] = pd.to_datetime(cases['date'])
    cases = cases.set_index('label')

    @parametrize(case=cases.index)
    def case_select(self, case):

        return self.cases.loc[case]


@pytest.mark.date_validator
@parametrize_with_cases("case", cases=DateCases)
def test_is_weekend_check(case):
    assert date_validator.is_weekend_check(case.date) == case.expected_is_weekend
