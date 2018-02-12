import requests
from xml.dom.minidom import *
from utils import saveCookies, loadCookies, log

class CBC:

    def __init__(self):
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if not session_cookies == None: 
            self.session.cookies = session_cookies 
        return


    def getImage(self, item):
        # ignore 'cbc$liveImage' - the pix don't make sense after the first load
        if 'defaultThumbnailUrl' in item:
            return item['defaultThumbnailUrl']
        elif 'cbc$staticImage' in item:
            return item['cbc$staticImage']
        elif 'cbc$featureImage' in item:
            return item['cbc$featureImage']


    def getLabels(self, item):
        labels = {
            'Studio': 'Canadian Broadcasting Corporation',
            'Country': 'Canada'
        }
        if 'cbc$callSign' in item:
            labels['ChannelName'] = item['cbc$callSign']
            labels['Title'] = '{} {}'.format(item['cbc$callSign'], item['title'])
        else:
            labels['Title'] = item['title']

        if 'cbc$show' in item:
            labels['TVShowTitle'] = item['cbc$show']

        if 'description' in item:
            labels['Plot'] = item['description']
            labels['PlotOutline'] = item['description']

        if 'cbc$liveDisplayCategory' in item:
            labels['Genre'] = item['cbc$liveDisplayCategory']
        return labels


    def parseSmil(self, smil):
        r = self.session.get(smil)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        dom = parseString(r.text)
        seq = dom.getElementsByTagName('seq')[0]
        video = seq.getElementsByTagName('video')[0]
        print video
        src = video.attributes['src'].value
        title = video.attributes['title'].value
        abstract = video.attributes['abstract'].value
        return src
