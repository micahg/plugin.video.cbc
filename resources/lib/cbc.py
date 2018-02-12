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


    def parseLiveChannel(self):
        return


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
