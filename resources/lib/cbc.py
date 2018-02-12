import requests
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

        json.loads(r.text)[self.LIST_ELEMENT]

        return