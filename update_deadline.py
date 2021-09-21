from datetime import datetime, timezone
from time_conversions import *


def update_deadline(gameweeks):
    curr_date = datetime.now(timezone.utc)
    msg = ""
    for deadline, name in gameweeks:
        secs = (deadline - curr_date).total_seconds()
        if secs > 0:
            hours = get_difference_in_hours(deadline, curr_date)
            if hours in [48, 24, 6, 2, 1]:
                msg = "Deadline for {} ({} Moscow Time) is in *{}*".format(name, utc_to_local(deadline).strftime(
                    '%d, %b %Y, %H:%M:%S'), parse_seconds((deadline - curr_date).total_seconds()))
                break
    return msg
