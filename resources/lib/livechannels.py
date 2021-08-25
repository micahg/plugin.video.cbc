"""Module for live channels."""
import json
from urllib.parse import urlencode

import requests

from resources.lib.utils import saveCookies, loadCookies, log
from resources.lib.cbc import CBC

LIST_URL = 'https://tpfeed.cbc.ca/f/ExhSPC/t_t3UKJR6MAT?pretty=true&sort=pubDate%7Cdesc'
LIST_ELEMENT = 'entries'


class LiveChannels:
    """Class for live channels."""

    def __init__(self):
        """Initialize the live channels class."""
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if session_cookies is not None:
            self.session.cookies = session_cookies

    def get_live_channels(self):
        """Get the list of live channels."""
        resp = self.session.get(LIST_URL)

        if not resp.status_code == 200:
            log('ERROR: {} returns status of {}'.format(LIST_URL, resp.status_code), True)
            return None
        saveCookies(self.session.cookies)

        items = json.loads(resp.content)[LIST_ELEMENT]
        return items

    def get_iptv_channels(self):
        """Get the channels in a IPTV Manager compatible list."""
        cbc = CBC()
        channels = self.get_live_channels()
        result = []
        for channel in channels:
            labels = cbc.get_labels(channel)
            image = cbc.getImage(channel)
            values = {
                'url': channel['content'][0]['url'],
                'image': image,
                'labels': urlencode(labels)
            }
            channel_dict = {
                'name': channel['title'],
                'stream': 'plugin://plugin.video.cbc/smil?' + urlencode(values),
                'id': channel['cbc$callSign'],
                'logo': image
            }

            # Use "CBC Toronto" instead of "Toronto"
            if len(channel_dict['name']) < 4 or channel_dict['name'][0:4] != 'CBC ':
                channel_dict['name'] = 'CBC {}'.format(channel_dict['name'])
            result.append(channel_dict)

        return result
