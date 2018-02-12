from resources.lib.utils import log
from resources.lib.livechannels import *
from resources.lib.liveprograms import *
from resources.lib.cbc import *
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urllib, urlparse

LIVE_CHANNELS = 'Live Channels'
LIVE_PROGRAMS = 'Live Programs'


def playSmil(smil):
    cbc = CBC()
    url = cbc.parseSmil(smil)
    p = xbmc.Player()
    p.play(url)
    return


def liveProgramsMenu():
    progs = LivePrograms()
    prog_list = progs.getLivePrograms()
    for prog in prog_list:
        # skip unavailable streams
        if not prog['availabilityState'] == 'available':
            continue
        elif prog['availableDate'] == 0:
            continue

        labels = {
            'Title': prog['title']
        }
        item = xbmcgui.ListItem(prog['title'])
        values = {
            'smil': prog['content'][0]['url']
        }
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + "?" + urllib.urlencode(values),
                                    listitem=item,
                                    isFolder=False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def liveChannelsMenu():
    chans = LiveChannels()
    chan_list = chans.getLiveChannels()
    for channel in chan_list:
        labels = {
            'Title': channel['cbc$callSign']
        }
        item = xbmcgui.ListItem(channel['cbc$callSign'])
        values = {
            'smil': channel['content'][0]['url']
        }
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + "?" + urllib.urlencode(values),
                                    listitem=item,
                                    isFolder=False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return

def mainMenu():

    for menu_item in [LIVE_CHANNELS, LIVE_PROGRAMS]:
        labels = { 'Title': menu_item }
        item = xbmcgui.ListItem(menu_item)
        item.setInfo(type="Video", infoLabels=labels)
        values = { 'menu': menu_item }
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + "?" + urllib.urlencode(values),
                                    listitem=item,
                                    isFolder=True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return


if len(sys.argv[2]) == 0:
    # create the data folder if it doesn't exist
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    mainMenu()
else:
    values = urlparse.parse_qs(sys.argv[2][1:])
    if 'menu' in values:
        menu = values['menu'][0]
        if menu == LIVE_CHANNELS:
            liveChannelsMenu()
        elif menu == LIVE_PROGRAMS:
            liveProgramsMenu()
    elif 'smil' in values:
        smil = values['smil'][0]
        playSmil(smil)
