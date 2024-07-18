"""Module for the V2 Gem API."""
import json

import requests

from resources.lib.cbc import CBC
from resources.lib.utils import loadAuthorization, log

LAYOUT_MAP = {
    # available in https://services.radio-canada.ca/ott/catalog/v2/gem/home?device=web&pageNumber=1&pageSize=7
    'featured': 'https://services.radio-canada.ca/ott/cbc-api/v2/home',
    # the rest are in https://services.radio-canada.ca/ott/catalog/v2/gem/browse?device=web
    'shows': 'https://services.radio-canada.ca/ott/cbc-api/v2/hubs/shows',
    'documentaries': 'https://services.radio-canada.ca/ott/cbc-api/v2/hubs/documentaries',
    'kids': 'https://services.radio-canada.ca/ott/cbc-api/v2/hubs/kids'
}
BROWSE_URI = 'https://services.radio-canada.ca/ott/catalog/v2/gem/browse?device=web'

# THIS CAN BE FILTERED, eg https://services.radio-canada.ca/ott/catalog/v2/gem/category/shows?device=web&filter=news-current-affairs
FORMAT_BY_ID = 'https://services.radio-canada.ca/ott/catalog/v2/gem/{}?device=web'
SHOW_BY_ID = 'https://services.radio-canada.ca/ott/cbc-api/v2/shows/{}'
CATEGORY_BY_ID = 'https://services.radio-canada.ca/ott/cbc-api/v2/categories/{}'
ASSET_BY_ID = 'https://services.radio-canada.ca/ott/cbc-api/v2/assets/{}'
SEARCH_BY_NAME = 'https://services.radio-canada.ca/ott/cbc-api/v2/search'

# api CONFIG IS AT https://services.radio-canada.ca/ott/catalog/v1/gem/settings?device=web

# THEY CALL https://services.radio-canada.ca/ott/catalog/v2/gem/browse?device=web 
# gives shows, films, docs ,etc



# THEY CALL https://services.radio-canada.ca/ott/catalog/v2/gem/browse?device=web

# THEY CALL https://services.radio-canada.ca/ott/catalog/v2/gem/category/shows?device=web&pageNumber=1&pageSize=80

# THEY CALL https://services.radio-canada.ca/ott/catalog/v2/gem/show/about-that-with-andrew-chang?device=web

# https://services.radio-canada.ca/ott/catalog/v2/gem/category/shows?device=web&filter=news-current-affairs&pageNumber=1&pageSize=80
#  https://gem.cbc.ca/_next/data/k8goGVAHx674mkof3HFCG/about-that-with-andrew-chang.json?show=about-that-with-andrew-chang

#   WE CALL https://services.radio-canada.ca/ott/cbc-api/v2/shows/about-that-with-andrew-chang
# THEY CALL https://services.radio-canada.ca/ott/catalog/v2/gem/show/about-that-with-andrew-chang?device=web

# https://services.radio-canada.ca/ott/external/v2/gem/mediaanalytics/about-that-with-andrew-chang/s01e10124297?device=web

#           https://services.radio-canada.ca/media/validation/v2/?appCode=gem&connectionType=hd&deviceType=ipad&idMedia=932803&multibitrate=true&output=json&tech=hls&manifestVersion=1&manifestType=desktop
# THEY CALL https://services.radio-canada.ca/media/validation/v2/?appCode=medianet&connectionType=hd&deviceType=ipad&idMedia=10124297&multibitrate=true&output=json&tech=hls&manifestType=desktop

# BETTER THINGS THEY CALL ...
# https://services.radio-canada.ca/ott/catalog/v2/gem/show/better-things?device=web&tier=Member
# https://services.radio-canada.ca/media/meta/v1/index.ashx?appCode=gem&idMedia=972969&output=jsonObject
# https://services.radio-canada.ca/media/validation/v2/?appCode=gem&connectionType=hd&deviceType=multiams&idMedia=972969&multibitrate=true&output=json&tech=azuremediaplayer&manifestVersion=1&manifestType=desktop
#
# CBC OTTAWA THEY CALL
# https://services.radio-canada.ca/media/validation/v2/?appCode=medianetlive&connectionType=hd&deviceType=ipad&idMedia=15732&multibitrate=true&output=json&tech=hls&manifestVersion=1&manifestType=desktop
#
# About that with andrew chang they call
# https://services.radio-canada.ca/ott/catalog/v2/gem/show/about-that-with-andrew-chang?device=web&tier=Member
# https://services.radio-canada.ca/media/validation/v2/?appCode=medianetlive&connectionType=hd&deviceType=ipad&idMedia=15732&multibitrate=true&output=json&tech=hls&manifestVersion=1&manifestType=desktop
#
# The appCode is a bit of mystery here... where do they get it (it changes for live tv and gem content)
# meta/v1/index.ashx is referenced in https://services.radio-canada.ca/ott/catalog/v1/gem/settings?device=web :
# streaming	
#   appCodeForVod	"gem"
#   appCodeForLive	"medianetlive"
#   appCodeForQuickturn	"medianet"
#
# medianetlive is returned in the json payload from https://services.radio-canada.ca/media/meta/v1/index.ashx?appCode=medianetlive&idMedia=15732&output=jsonObject
# but thats not helpful becuase we already knew it
#
# about that with andrew chang was medianet.
#
# I think if we can find an example quickturn that'll explain it
# 
# in the list of live channels, there is type: "live". mediaType differs for better-things and about-that-with-andrew-chang, eg:
# - https://services.radio-canada.ca/ott/catalog/v2/gem/show/about-that-with-andrew-chang?device=web&tier=Member (mediaType LiveToVod)
# - https://services.radio-canada.ca/ott/catalog/v2/gem/show/better-things?device=web&tier=Member (mediaType Episode)
#
# as best as i can tell, in https://gem.cbc.ca/_next/static/chunks/pages/_app-5b429e5ffa60c477.js, there is logic to decide appCode... its *really*
# hard to read but it seems like LiveToVod triggers appCodeForQuickturn, and otherwise, defaults to appCodeForVod
#
# https://services.radio-canada.ca/media/validation/v2/?appCode=gem         &connectionType=hd&deviceType=multiams&idMedia=972969&multibitrate=true&output=json&tech=azuremediaplayer&manifestVersion=1&manifestType=desktop
# https://services.radio-canada.ca/media/validation/v2/?appCode=medianetlive&connectionType=hd&deviceType=ipad    &idMedia=15732 &multibitrate=true&output=json&tech=hls             &manifestVersion=1&manifestType=desktop
# https://services.radio-canada.ca/media/validation/v2/?appCode=medianetlive&connectionType=hd&deviceType=ipad    &idMedia=15732 &multibitrate=true&output=json&tech=hls             &manifestVersion=1&manifestType=desktop



class GemV2:
    """V2 Gem API class."""

    @staticmethod
    def scrape_json(uri, headers=None):
        resp = CBC.get_session().get(uri, headers=headers)
        try:
            jsObj = json.loads(resp.content)
        except:
            log(f'Unable to parse result from {uri}', True)
            return None
        return jsObj

    @staticmethod
    def get_episode(url):
        """Get a Gem V2 episode by URL."""
        auth = loadAuthorization()

        # if we have no authorization, return none to for the UI to authorize
        if auth is None:
            return None

        headers = {}
        if 'token' in auth:
            headers['Authorization'] = 'Bearer {}'.format(auth['token'])

        if 'claims' in auth:
            headers['x-claims-token'] = auth['claims']

        return GemV2.scrape_json(url, headers)
        # resp = requests.get(url, headers=headers)
        # return json.loads(resp.content)

    @staticmethod
    def get_browse(type='formats'):
        """Get a Gem V2 API V2 browse format"""
        jsObj = GemV2.scrape_json(BROWSE_URI)
        if jsObj is not None and type in jsObj:
            return jsObj[type]
        log(f'Unable to find key "{type}" in response from {BROWSE_URI}')
        return None
    
    @staticmethod
    def get_format(path):
        """Get a Gem V2 API V2 browse format"""
        url = FORMAT_BY_ID.format(path)
        jsObj = GemV2.scrape_json(url)
        if jsObj is None or 'content' not in jsObj:
            log(f'Unable to find key content in response from {url}')
            return None
        content = jsObj['content'][0]
        if 'items' in content and 'results' in content['items']:
            return content['items']['results']
        
        if 'requestedType' in jsObj and jsObj['requestedType'].lower() == 'season':
            return content['lineups'][0]['items']
        if 'lineups' in content:
            return content['lineups']

        log(f'Unable to find key content/[0]/items/results in response from {url}')
        return None
    
    @staticmethod
    def get_stream(id, app_code):
        url = f'https://services.radio-canada.ca/media/meta/v1/index.ashx?appCode={app_code}&idMedia={id}&output=jsonObject'
        jsObj = GemV2.scrape_json(url)
        if jsObj['errorMessage'] is not None:
            log(f'Error fetching {url}: {jsObj["errorMessage"]}')
            return None
        
        drm = None
        for at in jsObj['availableTechs']:
            if at['name'] == 'dash':
                drm = at
            elif at['name'] == 'hls' and drm == None:
                # only use HLS if dash isn't available -- the new HLS cannot be played
                drm = at
        log(drm)
        tech = drm['name']
        manifest_versions = drm['manifestVersions']
        mv = manifest_versions[-1] if manifest_versions is not None else 1
        url = f'https://services.radio-canada.ca/media/validation/v2/?appCode={app_code}&connectionType=hd&deviceType=multiams&idMedia={id}&multibitrate=true&output=json&tech={tech}&manifestType=desktop&manifestVersion={mv}'
        retval = GemV2.get_episode(url)
        retval['type'] = drm['name']
        return retval
    
    @staticmethod
    def get_stream_drm(stream):
        wv_url = None
        wv_tok = None
        # https://cbcrcott-gem-key.akamaized.net/Widevine/?KID=23523b29-6eb6-4d94-9851-c71c38d25d9a
        #    https://rcavtoutv-key.akamaized.net/Widevine/?KID=23523b29-6eb6-4d94-9851-c71c38d25d9a
        for x in stream['params']:
            if x['name'] == 'widevineLicenseUrl':
                wv_url = x['value']
            if x['name'] == 'widevineAuthToken':
                wv_tok = x['value']
        return (wv_url, wv_tok)
    
    @staticmethod
    def normalized_format_item(item):
        """
        Given an object in the list returned by get_format, turn its useful
        bits into stuff we can display
        """
        images = item['images'] if 'images' in item else None
        retval = {
            'label': item['title'],
            'playable': 'idMedia' in item,
            'info_labels': {
                'tvshowtitle': item['title'],
                'title': item['title'],
            }
        }
        if 'description' in item:
            retval['info_labels']['plot'] = item['description']
            retval['info_labels']['plotoutline'] = item['description']
        if images:
            retval['art'] = {
                'thumb': images['background']['url'] if 'background' in images else None,
                'poster': images['card']['url'],
                'clearlogo': images['logo']['url'] if 'logo' in images else None,
            }
        if 'metadata' in item:
            meta = item['metadata']
            if 'country' in meta:
                retval['info_labels']['country'] = meta['country']
            if 'duration' in meta:
                retval['info_labels']['duration'] = meta['duration']
            if 'airDate' in meta:
                retval['info_labels']['aired'] = meta['airDate']
            if 'credits' in meta:
                retval['info_labels']['cast'] = meta['credits'][0]['peoples'].split(',')
        if 'idMedia' in item:
            retval['app_code'] = 'medianet' if item['mediaType'] == 'LiveToVod' else 'gem'
            None
        return retval

    @staticmethod
    def normalized_format_path(item):
        if 'idMedia' in item:
            return item['idMedia']
        if 'type' in item and item['type'].lower() == 'show':
            return f'{item["type"]}/{item["url"]}'
        return f'show/{item["url"]}'

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
    def get_asset_by_id(asset_id):
        url = ASSET_BY_ID.format(asset_id)
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)

    @staticmethod
    def get_category(category_id):
        """Get a Gem V2 category by ID."""
        # the results returned in items are duplicated and we should
        # filter out the ones where description is an empty string
        url = CATEGORY_BY_ID.format(category_id)
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)

    @staticmethod
    def get_labels(show, episode):
        """Get labels for a show."""
        labels = {
            'studio': 'Canadian Broadcasting Corporation',
            'country': 'Canada',
            'tvshowtitle': show['title'],
            'title': episode['title'],
            'plot': episode['description'],
            'plotoutline': episode['description'],
            'season': episode['season'],
        }
        if 'episode' in episode:
            labels['episode'] = episode['episode']
        if 'duration' in episode:
            labels['duration'] = episode['duration']
        return labels

    @staticmethod
    def search_by_term(term):
        params = {'term': term}
        resp = CBC.get_session().get(SEARCH_BY_NAME, params=params)
        return json.loads(resp.content)