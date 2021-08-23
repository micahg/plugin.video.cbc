"""Default plugin module."""
import os
from urllib.parse import urlencode, parse_qs, parse_qsl

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import inputstreamhelper
import routing

from resources.lib.cbc import CBC
from resources.lib.utils import log, getAuthorizationFile
from resources.lib.livechannels import LiveChannels
from resources.lib.liveprograms import LivePrograms
from resources.lib.shows import Shows, CBCAuthError

getString = xbmcaddon.Addon().getLocalizedString
LIVE_CHANNELS = getString(30004)
LIVE_PROGRAMS = getString(30005)
SHOWS = getString(30006)



# handle logout before using argv[1] as the addon handle
"""
if sys.argv[1] == 'logout':
    log('Logging out... {}'.format(sys.argv[1]), True)
    os.remove(getAuthorizationFile())
    sys.exit(0)
"""
plugin = routing.Plugin()


def authorize():
    """Authorize the client."""
    prog = xbmcgui.DialogProgress()
    prog.create(getString(30001))
    cbc = CBC()

    username = xbmcaddon.Addon().getSetting("username")
    if len(username) == 0:
        username = None

    password = xbmcaddon.Addon().getSetting("password")
    if len(password) == 0:
        password = None
        username = None

    if not cbc.authorize(username, password, prog.update):
        log('(authorize) unable to authorize', True)
        prog.close()
        xbmcgui.Dialog().ok(getString(30002), getString(30002))
        return False

    prog.close()
    return True


def play(labels, image, url):
    """Play the stream using the configured player."""
    item = xbmcgui.ListItem(labels['title'], path=url)
    item.setArt({'thumb': image, 'poster': image})
    item.setInfo(type="Video", infoLabels=labels)
    helper = inputstreamhelper.Helper('hls')
    if not xbmcaddon.Addon().getSettingBool("ffmpeg") and helper.check_inputstream():
        item.setProperty('inputstreamaddon', 'inputstream.adaptive')
        item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    xbmcplugin.setResolvedUrl(plugin.handle, True, item)


# def play_smil(smil, labels, image):
@plugin.route('/smil')
def play_smil():
    """Play an SMIL file."""
    log('MICAH args are {}'.format(plugin.args), True)
    cbc = CBC()
    url = cbc.parseSmil(plugin.args['url'][0])
    labels = dict(parse_qsl(plugin.args['labels'][0]))
    return play(labels, plugin.args['image'][0], url)


def play_show(values):
    """Play a show."""
    smil = values['smil'][0]
    image = values['image'][0]
    labels = values['labels'][0]
    labels = parse_qs(labels)
    for key in list(labels.keys()):
        labels[key] = labels[key][0]
    shows = Shows()
    try:
        res = shows.getStream(smil)
    except CBCAuthError as ex:
        log('(play_show) auth failed. retrying...', True)
        if not authorize():
            log('(play_show) auth retry failed: {}'.format(ex), True)
            return
        log('(play_show) auth retry successful', True)
        try:
            res = shows.getStream(smil)
        except CBCAuthError as ex:
            if ex.payment:
                log('(play_show) getStream failed because login required', True)
                xbmcgui.Dialog().ok(getString(30010), getString(30011))
            else:
                log('(play_show) getStream failed despite successful auth retry', True)
                xbmcgui.Dialog().ok(getString(30010), getString(30012))
            return

    return play(labels, image, res['url'])


@plugin.route('/programs')
def live_programs_menu():
    """Populate the menu with live programs."""
    xbmcplugin.setContent(plugin.handle, 'videos')
    progs = LivePrograms()
    prog_list = progs.getLivePrograms()
    cbc = CBC()
    for prog in prog_list:
        # skip unavailable streams
        if not prog['availabilityState'] == 'available':
            continue

        if prog['availableDate'] == 0:
            continue

        labels = cbc.getLabels(prog)
        image = cbc.getImage(prog)
        item = xbmcgui.ListItem(labels['title'])
        item.setArt({'thumb': image, 'poster': image})
        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true')
        values = {
            'smil': prog['content'][0]['url'],
            'labels': urlencode(labels),
            'image': image
        }
        url = sys.argv[0] + "?" + urlencode(values)
        xbmcplugin.addDirectoryItem(plugin.handle, url, item,False)

    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/channels')
def live_channels_menu():
    """Populate the menu with live channels."""
    xbmcplugin.setContent(plugin.handle, 'videos')
    chans = LiveChannels()
    chan_list = chans.getLiveChannels()
    cbc = CBC()
    for channel in chan_list:
        labels = cbc.getLabels(channel)
        image = cbc.getImage(channel)
        item = xbmcgui.ListItem(labels['title'])
        item.setArt({'thumb': image, 'poster': image})
        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(play_smil,
                                                                  url=channel['content'][0]['url'],
                                                                  labels=urlencode(labels),
                                                                  image=image),
                                    item, False)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/shows')
def play_menu():
    """Populate the menu with shows."""
    cbc = CBC()
    shows = Shows()
    if 'smil' in plugin.args:
        url = plugin.args['smil'][0]
    else:
        # if there is no smil link this is the main menu of all shows, so it
        # only has show titles (eg: not season or episode titles). In this
        # situation, it is appropriate to sort by title and ignore 'The ...'
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
        url = None

    prog = xbmcgui.DialogProgress()
    prog.create(getString(30003))
    try:
        show_list = shows.getShows(url, progress_callback=prog.update)
    except CBCAuthError:
        log('(play_menu) auth failed. retrying', True)
        if not authorize():
            log('(play_menu) auth retry failed', True)
            return
        log('(play_menu) auth retry successful', True)
        try:
            show_list = shows.getShows(url, progress_callback=prog.update)
        except CBCAuthError:
            log('(play_menu) getShows failed despite successful auth retry', True)
            return

    # if the first episode is video, assume all are video
    #is_video = 'video' in show_list[0]
    xbmcplugin.setContent(plugin.handle, 'episodes' if 'video' in show_list[0] else 'tvshows')

    log('MICAH show list is {}'.format(show_list), True)

    prog.close()
    for show in show_list:
        if show['url'] is None:
            continue
        is_video = show['video'] if 'video' in show else False
        labels = cbc.getLabels(show)
        image = show['image'] if 'image' in show else None
        item = xbmcgui.ListItem(labels['title'])

        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true' if is_video else 'false')
        if 'duration' in show:
            item.addStreamInfo('video', {'duration':show['duration']})
        item.setArt({'thumb': image, 'poster': image})
        # values = {
        #     'smil': show['url'],
        #     'video': show['video'] if is_video else None,
        #     'image': image
        # }
        #
        # if not values['video']:
        #     values['menu'] = SHOWS
        # else:
        #     values['labels'] = urlencode(labels)

        # plugin_url = sys.argv[0] + "?" + urlencode(values)
        # xbmcplugin.addDirectoryItem(plugin.handle, plugin_url, item, not is_video)
        # video = show['video'] if is_video else None
        if is_video:
            xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(play_smil,
                                                                      url=show['url'],
                                                                      labels=urlencode(labels),
                                                                      image=image),
                                        item, False)
        else:
            xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(play_menu, smil=show['url']), item, True)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/')
def main_menu():
    """Populate the menu with the main menu items."""
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    if not os.path.exists(getAuthorizationFile()):
        authorize()

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(live_channels_menu),
                                xbmcgui.ListItem(LIVE_CHANNELS), True)
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(live_programs_menu),
                                xbmcgui.ListItem(LIVE_PROGRAMS), True)
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(play_menu),
                                xbmcgui.ListItem(SHOWS), True)
    xbmcplugin.endOfDirectory(plugin.handle)

# ?menu=Live%20Channels
# ?menu=Live%20Programs
# ?menu=Shows
# ?image=None&menu=Shows&smil=https%3a%2f%2fapi-cbc.cloud.clearleap.com%2fcloffice%2fclient%2fweb%2fbrowse%2fe8e1db08-1e3c-4221-8b43-f50f32606ce6&video=None
"""
log('MICAH path is "{}"'.format(sys.argv[2]), True)
if len(sys.argv[2]) == 0:
    # create the data folder if it doesn't exist
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    if not os.path.exists(getAuthorizationFile()):
        authorize()

    main_menu()
else:
    values = parse_qs(sys.argv[2][1:])
    if 'video' in values and values['video'][0] == 'True':
        play_show(values)
    elif 'menu' in values:
        menu = values['menu'][0]
        if menu == LIVE_CHANNELS:
            liveChannelsMenu()
        elif menu == LIVE_PROGRAMS:
            liveProgramsMenu()
        elif menu == SHOWS:
            play_menu(values)
    elif 'smil' in values:
        play_smil(values['smil'][0], dict(parse_qsl(values['labels'][0])), values['image'][0])
"""

if __name__ == '__main__':
    plugin.run()
