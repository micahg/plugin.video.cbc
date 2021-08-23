"""Module for live channels."""
import json
from urllib.parse import urlencode

import requests

from .utils import saveCookies, loadCookies, log
from resources.lib.cbc import CBC


class LiveChannels:
    """Class for live channels."""
    def __init__(self):
        """Initialize the live channels class."""
        self.LIST_URL = 'http://tpfeed.cbc.ca/f/ExhSPC/t_t3UKJR6MAT?pretty=true&sort=pubDate%7Cdesc'
        self.LIST_ELEMENT = 'entries'

        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if not session_cookies == None:
            self.session.cookies = session_cookies


    def get_live_channels(self):
        r = self.session.get(self.LIST_URL)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        items = json.loads(r.content)[self.LIST_ELEMENT]
        return items

    def get_iptv_channels(self):
        """Get the channels in a IPTV Manager compatible list."""
        cbc = CBC()
        channels = self.get_live_channels()
        # [ {'name': channel.name, 'stream': channel.} for channel in channels ]
        result = []
        log('MICAH IPTV REQUEST FOR CHANNELS IS {}'.format(channels), True)
        for channel in channels:
            log('MICAH CHANNEL IS {}'.format(channel), True)
            labels = cbc.getLabels(channel)
            values = {
                'url': channel['content'][0]['url'],
                'image': channel['cbc$staticImage'],
                'labels': urlencode(labels)
            }
            channel_dict = {
                'name': channel['title'],
                'stream': 'plugin://plugin.video.cbc/smil?' + urlencode(values),
                'id': channel['cbc$callSign'],
                'logo': channel['cbc$staticImage']
            }
            result.append(channel_dict)
        log('MICAH IPTV RETURNING {}'.format(result), True)
        return result
