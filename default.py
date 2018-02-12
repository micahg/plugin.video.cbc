from resources.lib.utils import log
from resources.lib.livechannels import *
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urllib, urlparse

LIVE_CHANNELS = 'Live Channels'


def liveChannelsMenu():
    log('Micah live channels menu', True)
    chans = LiveChannels()
    chan_list = chans.getLiveChannels()
    for channel in chan_list:
        #print '{} {}: {}'.format(item['cbc$callSign'], item['title'], item['description'])
        #print item['content'][0]['url'] + '\n'
        labels = {
            'Title': channel['cbc$callSign']
        }
        item = xbmcgui.ListItem(channel['cbc$callSign'])
        #item = xbmcgui.ListItem(channel['cbc$callSign'])
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
    labels = { 'Title': LIVE_CHANNELS }
    item = xbmcgui.ListItem(LIVE_CHANNELS)
    item.setInfo(type="Video", infoLabels=labels)
    values = { 'menu': LIVE_CHANNELS }
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
    log('MICAH values = {}'.format(values), True)
    if 'menu' in values:
        if values['menu'][0] == LIVE_CHANNELS:
            liveChannelsMenu()
    elif 'smil' in values:
        smil = values['smil'][0]
        log('MICAH smil = {}'.format(smil), True)
