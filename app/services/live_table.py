import requests
from bs4 import BeautifulSoup

from .config import get_league_mapping, get_players_mapping

ATTRIBUTES = [
    "total",
    "gw",
    "hit",
    "chip",
    "cap",
    "vc",
]


def printf(format, *args):
    return (format % args)


def get_live_table(chat_id):
    try:
        league_mapping = get_league_mapping()
        chat_key = str(int(chat_id))
        if chat_key not in league_mapping:
            return "Live table is not supported for this chat"

        league_code = str(league_mapping[chat_key])
        players_mapping_all = get_players_mapping()
        players_mapping = players_mapping_all.get(league_code)
        if not players_mapping:
            return "Live table is not configured for this league"

        response = requests.get(f"https://www2.livefpl.net/leagues/{league_code}", allow_redirects=False, timeout=20)
        if response.status_code != 200:
            return "Live table is not available now"
        htmlText = response.text
        page = BeautifulSoup(htmlText, "html.parser")

        res = []
        for playerId, (name, teamName) in players_mapping.items():
            data = {
                "name": name,
                "team": teamName,
            }
            for attribute in ATTRIBUTES:
                element = page.find(id=f"{playerId}_{attribute}")
                if not element:
                    # If livefpl layout changes, fail gracefully
                    return "Live table is not available now"
                value = element.get_text()
                data[attribute] = value
            res.append(data)

        res.sort(key=lambda attr: int(attr["total"]), reverse=True)

        msg = printf("%2.2s|%12.12s|%5.5s|%3.3s\n\n", "#",  "Player", "Total", "GW")
        for i, player in enumerate(res):
            try:
                name, last_name = player['name'].split(" ")
                display = f"{name} {last_name[0]}."
            except Exception:
                display = player['name']
            playerMessage = printf("%2.2s|%12.12s|%5.5s|%3.3s\n", i + 1, display, player['total'], player['gw'])
            playerMessage = playerMessage.replace("-", "\\-").replace("|", "\\|")
            msg += playerMessage
    except Exception:
        return "Live table is not available now"

    return "```" + msg + "```" 