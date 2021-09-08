"""Electronic program guide module."""
from datetime import datetime

import requests

from resources.lib.utils import log
from resources.lib.cbc import CBC
from resources.lib.livechannels import LiveChannels

# Y/M/D
GUIDE_URL_FMT = 'https://www.cbc.ca/programguide/daily/{}/cbc_television'


def get_iptv_epg():
    """Get the EPG Data."""
    log("MICAH in get_iptv_epg HELLO", True)
    live = LiveChannels()
    channels = live.get_live_channels()
    blocked = live.get_blocked_iptv_channels()
    unblocked = []
    log('Blocked for guide {}'.format(blocked), True)
    for channel in channels:
        if CBC.get_callsign(channel) not in blocked:
            unblocked.append(channel)
    log('Remaining channels for EPG are {}'.format(unblocked), True)
    data = call_guide_url(datetime.now())
    log('MICAH DATA IS {}'.format(data), True)

    # return []


def call_guide_url(dttm):
    """Call the guide URL and return the response body."""
    date_str = dttm.strftime('%Y/%m/%d')
    url = GUIDE_URL_FMT.format(date_str)
    log('CALLING {}'.format(url))
    resp = requests.get(url)
    if resp.status_code != 200:
        log('ERROR: {} returns status of {}'.format(url, resp.status_code), True)
        return None
    return resp.content
