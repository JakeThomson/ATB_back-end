import datetime as dt
import sys
sys.path.append("../")
import pandas_market_calendars as mcal


def is_weekend_check(date):
    """ Checks if date is a weekend.

    :param date: Datetime object to be checked.
    :return: True if date is a weekend, False if weekday
    """
    if date.weekday() == 6 or date.weekday() == 5:
        return True
    else:
        return False


def is_holiday_check(date):
    """ Checks if date falls on a holiday (banks closed).

    :param date: Datetime object to be checked.
    :return: True if date is a holiday, False if not
    """
    nyse = mcal.get_calendar('NYSE')
    us_holidays = nyse.holidays().holidays

    if date.date() in us_holidays:
        return True
    else:
        return False


def validate_date(date, direction=1):
    """ Checks the date and ensures it is valid to be used within the system (not a weekend or holiday). If it is not
    valid, then it corrects the date by pushing the date back or forward a day or more.

    :param date: Datetime object to be checked.
    :param direction: Integer value to determine what direction in time to apply correction.
        +1 (default) to correct the date forwards in time, -1 to correct backwards.
    :return date: A valid datetime object.
    """

    if direction == 1 or direction == -1:
        initial_date = date
        invalid = is_holiday_check(date) or is_weekend_check(date)

        # Keep adjusting date until it is valid.
        while invalid:
            if is_holiday_check(date) or is_weekend_check(date):
                date = date + (dt.timedelta(days=1) * direction)
            else:
                invalid = False
        return date
    else:
        raise ValueError("Direction argument in cleanse_date method can only be 1 or -1.")
