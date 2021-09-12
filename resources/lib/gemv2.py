"""Module for the V2 Gem API."""
import json

from resources.lib.cbc import CBC

LAYOUT_MAP = {
    'featured': 'https://services.radio-canada.ca/ott/cbc-api/v2/home'
}


class GemV2:
    """V2 Gem API class."""

    @staticmethod
    def get_layout(name):
        """Get a Gem V2 layout by name."""
        url = LAYOUT_MAP[name]
        resp = CBC.get_session().get(url)
        json.loads(resp.content)
