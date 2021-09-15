"""Module for the V2 Gem API."""
import json

from resources.lib.cbc import CBC

LAYOUT_MAP = {
    'featured': 'https://services.radio-canada.ca/ott/cbc-api/v2/home'
}
SHOW_BY_ID = 'https://services.radio-canada.ca/ott/cbc-api/v2/shows/{}'


class GemV2:
    """V2 Gem API class."""

    @staticmethod
    def get_layout(name):
        """Get a Gem V2 layout by name."""
        url = LAYOUT_MAP[name]
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)

    @staticmethod
    def get_show_layout_by_id(show_id):
        """Get a Gem V2 show layout by ID."""
        url = SHOW_BY_ID.format(show_id)
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)

    @staticmethod
    def get_episode(url):
        """Get a Gem V2 episode by URL."""
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)
