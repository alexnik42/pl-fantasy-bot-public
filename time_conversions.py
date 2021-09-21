import pytz


def parse_seconds(n):
    day = n // (24 * 3600)

    n = n % (24 * 3600)
    hour = n // 3600

    n %= 3600
    minutes = n // 60

    n %= 60
    seconds = n
    return (str(int(day)) + " days, " + str(int(hour)) + " hours, " + str(int(minutes)) + " minutes, " + str(int(seconds)) + " seconds")


def utc_to_local(utc_dt):
    tz = pytz.timezone('Europe/Moscow')
    return utc_dt.astimezone(tz)


def get_difference_in_hours(deadline, curr_date):
    hours = (deadline - curr_date).total_seconds() // 3600
    return hours
