import requests
import logging
from bs4 import BeautifulSoup

from .config import get_league_mapping, get_players_mapping

logging.getLogger().setLevel(logging.INFO)

ATTRIBUTES = [
    "data-total",
    "data-gw"
]


def printf(format, *args):
    return (format % args)


def get_live_table(chat_id):
    logging.info("Getting live table for chat_id: %s", chat_id)
    try:
        league_mapping = get_league_mapping()
        chat_key = str(int(chat_id))
        logging.debug("Looking up league mapping for chat_key: %s", chat_key)
        
        if chat_key not in league_mapping:
            logging.error("No league mapping found for chat_key: %s", chat_key)
            return "Live table is not supported for this chat"

        league_code = str(league_mapping[chat_key])
        logging.info("Found league_code: %s for chat_id: %s", league_code, chat_id)
        
        players_mapping_all = get_players_mapping()
        logging.info("Players mapping: %s", players_mapping_all)
        players_mapping = players_mapping_all.get(league_code)
        if not players_mapping:
            logging.error("No Players mapping found for league: %s", league_code)
            return "Live table is not configured for this league"

        # List of URLs to try in order of preference
        urls_to_try = [
            f"https://www2.livefpl.net/leagues/{league_code}",
            f"https://plan.livefpl.net/leagues/{league_code}"
        ]
        
        response = None
        htmlText = None
        page = None
        
        for url in urls_to_try:
            try:
                logging.info("Trying URL: %s for league: %s", url, league_code)
                response = requests.get(url, allow_redirects=True, timeout=20)
                if response.status_code == 200:
                    logging.info("Successfully fetched data from: %s", url)
                    htmlText = response.text
                    page = BeautifulSoup(htmlText, "html.parser")
                    break
                else:
                    logging.warning("Failed to fetch from %s. Status code: %s", url, response.status_code)
            except Exception as e:
                logging.warning("Exception when trying %s: %s", url, str(e))
                continue
        
        if response is None or response.status_code != 200:
            response_msg = "Live table is not available now"
            logging.error("All URLs failed for league: %s. Returning: %s", league_code, response_msg)
            return response_msg

        res = []
        for playerId, (name, teamName) in players_mapping.items():
            logging.debug("Processing player: %s (ID: %s, Team: %s)", name, playerId, teamName)
            data = {
                "name": name,
                "team": teamName,
            }
            for attribute in ATTRIBUTES:
                # Find element with data-fpl-id matching playerId
                element = page.find(attrs={"data-fpl-id": playerId})
                if not element:
                    response_msg = "Live table is not available now"
                    logging.error("Missing element for player %s. Livefpl layout may have changed. Returning: %s", playerId, response_msg)
                    # If livefpl layout changes, fail gracefully
                    return response_msg
                
                # Get the value of the specific attribute
                value = element.get(attribute)
                if value is None:
                    response_msg = "Live table is not available now"
                    logging.error("Missing attribute %s for player %s. Livefpl layout may have changed. Returning: %s", attribute, playerId, response_msg)
                    # If livefpl layout changes, fail gracefully
                    return response_msg
                
                # Extract the attribute name without 'data-' prefix for the data dictionary
                attr_name = attribute.replace('data-', '')
                data[attr_name] = value
            res.append(data)

        res.sort(key=lambda attr: int(attr["total"]), reverse=True)

        msg = printf("%2.2s|%12.12s|%5.5s|%3.3s\n\n", "#",  "Player", "Total", "GW")
        for i, player in enumerate(res):
            try:
                name, last_name = player['name'].split(" ")
                display = f"{name} {last_name[0]}."
            except Exception:
                logging.debug("Could not split player name: %s, using full name", player['name'])
                display = player['name']
            playerMessage = printf("%2.2s|%12.12s|%5.5s|%3.3s\n", i + 1, display, player['total'], player['gw'])
            playerMessage = playerMessage.replace("-", "\\-").replace("|", "\\|")
            msg += playerMessage
        
        logging.info("Successfully generated live table for chat_id: %s with %d players", chat_id, len(res))
    except Exception as e:
        response_msg = "Live table is not available now"
        logging.error("Error getting live table for chat_id %s: %s. Returning: %s", chat_id, e, response_msg, exc_info=True)
        return response_msg

    final_response = "```" + msg + "```"
    return final_response 