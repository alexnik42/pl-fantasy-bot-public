import requests
import dateutil.parser


def parse_gameweeks():
    res = requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/")
    res = res.json()
    gameweeks = [(dateutil.parser.isoparse(
        r["deadline_time"]),  r["name"]) for r in res["events"]]
    return gameweeks
