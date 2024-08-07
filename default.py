"""Default plugin module."""
import os
import json
from urllib.parse import urlencode, parse_qsl

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
from xbmcvfs import translatePath
import inputstreamhelper
import routing

from resources.lib.cbc import CBC
from resources.lib.utils import log, getAuthorizationFile, get_cookie_file, get_iptv_channels_file
from resources.lib.livechannels import LiveChannels
from resources.lib.gemv2 import GemV2
from resources.lib.iptvmanager import IPTVManager

getString = xbmcaddon.Addon().getLocalizedString
LIVE_CHANNELS = getString(30004)
GEMS = {
    'featured': getString(30005),
    'shows': getString(30006),
    'documentaries': getString(30024),
    'kids': getString(30025)
}
SEARCH = getString(30026)


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

    if not cbc.azure_authorize(username, password, prog.update):
        log('(authorize) unable to authorize', True)
        prog.close()
        xbmcgui.Dialog().ok(getString(30002), getString(30002))
        return False

    prog.close()
    return True


def play(labels, image, url):
    """Play the stream using the configured player."""
    item = xbmcgui.ListItem(labels['title'], path=url)
    if image:
        item.setArt({'thumb': image, 'poster': image})
    item.setInfo(type="Video", infoLabels=labels)
    helper = inputstreamhelper.Helper('hls')
    if not xbmcaddon.Addon().getSettingBool("ffmpeg") and helper.check_inputstream():
        item.setProperty('inputstream', 'inputstream.adaptive')
        item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    xbmcplugin.setResolvedUrl(plugin.handle, True, item)
    if url is None:
        xbmcgui.Dialog().ok(getString(30010), getString(30011))

    
def add_items(handle, items):
    for item in items:
        list_item = xbmcgui.ListItem(item['title'])
        list_item.setInfo(type="Video", infoLabels=CBC.get_labels(item))
        image = item['image'].replace('(Size)', '224')
        list_item.setArt({'thumb': image, 'poster': image})
        item_type = item['type']
        is_folder = True
        if item_type == 'SHOW':
            url = plugin.url_for(gem_show_menu, item['id'])
        elif item_type == 'ASSET':
            url = plugin.url_for(gem_asset, item['id'])
            list_item.setProperty('IsPlayable', 'true')
            is_folder = False
        elif item_type == 'SEASON':
            # ignore the season and go to the show (its what the web UI does)
            url = plugin.url_for(gem_show_menu, item['id'].split('/')[0])
        else:
            log(f'Unable to handle shelf item type "{item_type}".', True)
            url = None
        xbmcplugin.addDirectoryItem(handle, url, list_item, is_folder)


@plugin.route('/logout')
def logout():
    """Remove authorization stuff."""
    log('Logging out...', True)
    os.remove(getAuthorizationFile())
    os.remove(get_cookie_file())


@plugin.route('/iptv/channels')
def iptv_channels():
    """Send a list of IPTV channels."""
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_channels()


@plugin.route('/iptv/epg')
def iptv_epg():
    """Get EPG information for IPTV manager."""
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_epg()


@plugin.route('/iptv/addall')
def live_channels_add_all():
    """Add all channels back to the PVR listing."""
    os.remove(get_iptv_channels_file())


@plugin.route('/iptv/add/<station>')
def live_channels_add(station):
    """Add a single station."""
    LiveChannels.add_iptv_channel(station)


@plugin.route('/iptv/remove/<station>')
def live_channels_remove(station):
    """Remove a station."""
    LiveChannels.remove_iptv_channel(station)


@plugin.route('/iptv/addonly/<station>')
def live_channels_add_only(station):
    """Remove all but the specified station from the IPTV station list."""
    LiveChannels.add_only_iptv_channel(station)


@plugin.route('/channels/play')
def play_live_channel():
    labels = dict(parse_qsl(plugin.args['labels'][0])) if 'labels' in plugin.args else None
    chans = LiveChannels()
    url = chans.get_channel_stream(plugin.args['id'][0])
    return play(labels, plugin.args['image'][0], url)

@plugin.route('/channels')
def live_channels_menu():
    """Populate the menu with live channels."""
    xbmcplugin.setContent(plugin.handle, 'videos')
    chans = LiveChannels()
    chan_list = chans.get_live_channels()
    cbc = CBC()
    for channel in chan_list:
        labels = CBC.get_labels(channel)
        callsign = cbc.get_callsign(channel)
        image = cbc.get_image(channel)
        item = xbmcgui.ListItem(labels['title'])
        item.setArt({'thumb': image, 'poster': image})
        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true')
        item.addContextMenuItems([
            (getString(30014), 'RunPlugin({})'.format(plugin.url_for(live_channels_add_all))),
            (getString(30015), 'RunPlugin({})'.format(plugin.url_for(live_channels_add, callsign))),
            (getString(30016), 'RunPlugin({})'.format(plugin.url_for(live_channels_remove, callsign))),
            (getString(30017), 'RunPlugin({})'.format(plugin.url_for(live_channels_add_only, callsign))),
        ])
        xbmcplugin.addDirectoryItem(plugin.handle,
                                    plugin.url_for(play_live_channel, id=channel['idMedia'],
                                                   labels=urlencode(labels), image=image), item, False)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/gem/show/episode')
def gem_episode():
    """Play an episode."""
    json_str = plugin.args['query'][0]
    episode = json.loads(json_str)

    # get the url, and failing that, attempt authorization, then retry
    resp = GemV2().get_episode(episode['url'])
    url = None if not resp else resp['url'] if 'url' in resp else None
    if not url:
        log('Failed to get stream URL, attempting to authorize.')
        if authorize():
            resp = GemV2().get_episode(episode['url'])
            url = resp['url'] if 'url' in resp else None

    labels = episode['labels']
    play(labels, None, url)


@plugin.route('/gem/show/season')
def gem_show_season():
    """Create a menu for a show season."""
    xbmcplugin.setContent(plugin.handle, 'videos')
    json_str = plugin.args['query'][0]
    # remember show['season'] is season details but there is general show info in show as well
    show = json.loads(json_str)
    for episode in show['season']['assets']:
        item = xbmcgui.ListItem(episode['title'])
        image = episode['image'].replace('(Size)', '224')
        item.setArt({'thumb': image, 'poster': image})
        item.setProperty('IsPlayable', 'true')
        labels = GemV2.get_labels(show, episode)
        item.setInfo(type="Video", infoLabels=labels)
        episode_info = {'url': episode['playSession']['url'], 'labels': labels}
        url = plugin.url_for(gem_episode, query=json.dumps(episode_info))
        xbmcplugin.addDirectoryItem(plugin.handle, url, item, False)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/gem/asset/<path:asset>')
def gem_asset(asset):
    asset_layout = GemV2.get_asset_by_id(asset)
    resp = GemV2.get_episode(asset_layout['playSession']['url'])
    url = None if not resp else resp['url'] if 'url' in resp else None
    if not url:
        log('Failed to get stream URL, attempting to authorize.')
        if authorize():
            resp = GemV2().get_episode(asset_layout['playSession']['url'])
            url = resp['url'] if 'url' in resp else None
    labels = GemV2.get_labels({'title': asset_layout['series']}, asset_layout)
    image = asset_layout['image']
    play(labels, image, url)


def gem_add_film_assets(assets):
    for asset in assets:
        labels = GemV2.get_labels({'title': asset['series']}, asset)
        image = asset['image']
        item = xbmcgui.ListItem(labels['title'])
        item.setInfo(type="Video", infoLabels=labels)
        item.setArt({'thumb': image, 'poster': image})
        item.setProperty('IsPlayable', 'true')
        episode_info = {'url': asset['playSession']['url'], 'labels': labels}
        url = plugin.url_for(gem_episode, query=json.dumps(episode_info))
        xbmcplugin.addDirectoryItem(plugin.handle, url, item, False)


@plugin.route('/gem/show/<show_id>')
def gem_show_menu(show_id):
    """Create a menu for a shelfs items."""
    xbmcplugin.setContent(plugin.handle, 'videos')
    show_layout = GemV2.get_show_layout_by_id(show_id)
    show = {k: v for (k, v) in show_layout.items() if k not in ['sponsors', 'seasons']}
    for season in show_layout['seasons']:

        # films seem to have been shoe-horned (with teeth) into the structure oddly -- compensate
        if season['title'] == 'Film':
            gem_add_film_assets(season['assets'])
        else:
            labels = GemV2.get_labels(season, season)
            item = xbmcgui.ListItem(season['title'])
            item.setInfo(type="Video", infoLabels=labels)
            image = season['image'].replace('(Size)', '224')
            item.setArt({'thumb': image, 'poster': image})
            show['season'] = season
            url = plugin.url_for(gem_show_season, query=json.dumps(show))
            xbmcplugin.addDirectoryItem(plugin.handle, url, item, True)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/gem/shelf')
def gem_shelf_menu():
    """Create a menu item for each shelf."""
    handle = plugin.handle
    xbmcplugin.setContent(handle, 'videos')
    json_str = plugin.args['query'][0]
    shelf_items = json.loads(json_str)
    add_items(handle, shelf_items)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)


@plugin.route('/gem/categories/<category_id>')
def gem_category_menu(category_id):
    """Populate a menu with categorical content."""
    handle = plugin.handle
    xbmcplugin.setContent(handle, 'videos')
    category = GemV2.get_category(category_id)
    for show in category['items']:
        item = xbmcgui.ListItem(show['title'])
        item.setInfo(type="Video", infoLabels=CBC.get_labels(show))
        image = show['image'].replace('(Size)', '224')
        item.setArt({'thumb': image, 'poster': image})
        url = plugin.url_for(gem_show_menu, show['id'])
        xbmcplugin.addDirectoryItem(handle, url, item, True)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)


@plugin.route('/gem/search')
def search():
    handle = plugin.handle
    term = xbmcgui.Dialog().input(SEARCH, type=xbmcgui.INPUT_ALPHANUM)
    results = GemV2.search_by_term(term)
    add_items(handle, results)
    xbmcplugin.endOfDirectory(handle)


@plugin.route('/gem/layout/<layout>')
def layout_menu(layout):
    """Populate the menu with featured items."""
    handle = plugin.handle
    xbmcplugin.setContent(handle, 'videos')
    layout = GemV2.get_layout(layout)
    if 'categories' in layout:
        for category in layout['categories']:
            item = xbmcgui.ListItem(category['title'])
            url = plugin.url_for(gem_category_menu, category['id'])
            xbmcplugin.addDirectoryItem(handle, url, item, True)
    if 'shelves' in layout:
        for shelf in layout['shelves']:
            item = xbmcgui.ListItem(shelf['title'])
            shelf_items = json.dumps(shelf['items'])
            url = plugin.url_for(gem_shelf_menu, query=shelf_items)
            xbmcplugin.addDirectoryItem(handle, url, item, True)
    xbmcplugin.endOfDirectory(handle)


@plugin.route('/')
def main_menu():
    """Populate the menu with the main menu items."""
    data_path = translatePath('special://userdata/addon_data/plugin.video.cbc')
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    if not os.path.exists(getAuthorizationFile()):
        authorize()

    handle = plugin.handle
    xbmcplugin.setContent(handle, 'videos')
    for key, value in GEMS.items():
        xbmcplugin.addDirectoryItem(handle, plugin.url_for(layout_menu, key), xbmcgui.ListItem(value), True)
    xbmcplugin.addDirectoryItem(handle, plugin.url_for(live_channels_menu), xbmcgui.ListItem(LIVE_CHANNELS), True)
    xbmcplugin.addDirectoryItem(handle, plugin.url_for(search), xbmcgui.ListItem(SEARCH), True)
    xbmcplugin.endOfDirectory(handle)


if __name__ == '__main__':
    plugin.run()
