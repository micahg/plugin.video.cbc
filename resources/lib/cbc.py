"""Module for general CBC stuff"""
from uuid import uuid4
from base64 import b64encode, b64decode
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
import urllib.request
import urllib.parse
import urllib.error
import json
from xml.dom.minidom import *
import xml.etree.ElementTree as ET

import requests

from .utils import save_cookies, loadCookies, saveAuthorization, log

CALLSIGN = 'cbc$callSign'
API_KEY = '3f4beddd-2061-49b0-ae80-6f1f2ed65b37'
SCOPES = 'openid '\
        'offline_access '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/email '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.create '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.delete '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.info '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.modify '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.reset-password '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.send-confirmation-email '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.write '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/media-drmt '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/media-meta '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/media-validation '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/media-validation.read '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/metrik '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/oidc4ropc '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/ott-profiling '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/ott-subscription '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/profile '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/subscriptions.validate '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/subscriptions.write '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/toutv '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/toutv-presentation '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/toutv-profiling '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/testapiwithjwtendpoint.admin '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.info'
AUTHORIZE_LOGIN = 'https://login.cbc.radio-canada.ca/bef1b538-1950-4283-9b27-b096cbc18070/B2C_1A_ExternalClient_FrontEnd_Login_CBC/oauth2/v2.0/authorize'
SELF_ASSERTED_LOGIN = 'https://login.cbc.radio-canada.ca/bef1b538-1950-4283-9b27-b096cbc18070/B2C_1A_ExternalClient_FrontEnd_Login_CBC/SelfAsserted'
CONFIRM_LOGIN = 'https://login.cbc.radio-canada.ca/bef1b538-1950-4283-9b27-b096cbc18070/B2C_1A_ExternalClient_FrontEnd_Login_CBC/api/SelfAsserted/confirmed'
SIGNIN_LOGIN = 'https://login.cbc.radio-canada.ca/bef1b538-1950-4283-9b27-b096cbc18070/B2C_1A_ExternalClient_FrontEnd_Login_CBC/api/CombinedSigninAndSignup/confirmed'
RADIUS_LOGIN_FMT = 'https://api.loginradius.com/identity/v2/auth/login?{}'
RADIUS_JWT_FMT = 'https://cloud-api.loginradius.com/sso/jwt/api/token?{}'
TOKEN_URL = 'https://services.radio-canada.ca/ott/cbc-api/v2/token'
PROFILE_URL = 'https://services.radio-canada.ca/ott/cbc-api/v2/profile'


class CBC:
    """Class for CBC stuff."""

    def __init__(self):
        """Initialize the CBC class."""
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if session_cookies is not None:
            self.session.cookies = session_cookies

    @staticmethod
    def azure_authorize_authorize(sess: requests.Session):
        """
        Make the first authorization call.
        @param sess A requests session
        """
        nonce= str(uuid4())
        guid = str(uuid4())
        state_str = f'{guid}|{{"action":"login","returnUrl":"/","fromSubscription":false}}'.encode()
        state = b64encode(state_str).decode('ascii')
        params = {
            'client_id': 'fc05b0ee-3865-4400-a3cc-3da82c330c23',
            'nonce': nonce,
            'redirect_uri': 'https://gem.cbc.ca/auth-changed',
            'scope': SCOPES,
            'response_type': 'id_token token',
            'response_mode': 'fragment',
            'prompt': 'login',
            'state': state,
            'state_value': state,
            'ui_locales': 'en',
        }
        resp = sess.get(AUTHORIZE_LOGIN, params=params)
        if resp.status_code != 200:
            log('Call to authorize fails', True)
            return False

        return True


    @staticmethod
    def azure_authorize_self_asserted(sess: requests.Session, username: str, password: str, csrf: str, tx_arg: str):
        """
        Make the second authorization call.
        @param sess The requests session
        """

        headers = { 'x-csrf-token': csrf }
        params = { 'tx': tx_arg, 'p': 'B2C_1A_ExternalClient_FrontEnd_Login_CBC' }
        data = { 'request_type': 'RESPONSE', 'email': username, 'password': password }

        resp = sess.post(SELF_ASSERTED_LOGIN, params=params, headers=headers, data=data)
        if not resp.status_code == 200:
            log('Call to SelfAsserted fails', True)
            return False
        return True


    @staticmethod
    def azure_authorize_confirmed(sess: requests.Session, csrf: str, tx_arg: str):
        """
        Make the third authorization call.
        @param sess The requests session
        @param csrf The csrf token
        @param tx_arg the tx parameter
        """
        # headers = { 'x-csrf-token': csrf }
        params = {
            'tx': tx_arg,
            'p': 'B2C_1A_ExternalClient_FrontEnd_Login_CBC',
            'csrf_token': csrf,
            # 'diags': '{"pageViewId":"69fffafd-f95b-457b-a277-8df3b7a59c72","pageId":"CombinedSigninAndSignup","trace":[{"ac":"T005","acST":1681150201,"acD":1},{"ac":"T021 - URL:https://micro-sites.radio-canada.ca/b2cpagelayouts/login/password?ui_locales=en&azpContext=cbcgem","acST":1681150201,"acD":30},{"ac":"T019","acST":1681150201,"acD":5},{"ac":"T004","acST":1681150201,"acD":3},{"ac":"T003","acST":1681150201,"acD":1},{"ac":"T035","acST":1681150202,"acD":0},{"ac":"T030Online","acST":1681150202,"acD":0},{"ac":"T002","acST":1681150208,"acD":0},{"ac":"T018T010","acST":1681150208,"acD":493}]}',
        }

        resp = sess.get(CONFIRM_LOGIN, params=params)
        if resp.status_code != 200:
            log('Call to authorize fails', True)
            return False

        return True

    @staticmethod
    def azure_authorize_sign_in(sess: requests.Session, csrf: str, tx_arg: str):
        """
        Make the third authorization call.
        @param sess The requests session
        @param csrf The csrf token
        @param tx_arg the tx parameter
        """
        params = {
            'tx': tx_arg,
            'p': 'B2C_1A_ExternalClient_FrontEnd_Login_CBC',
            'csrf_token': csrf,
            'rememberMe': 'true',
        }

        resp = sess.get(SIGNIN_LOGIN, params=params)
        if resp.status_code != 200:
            log('Call to authorize fails', True)
            return False

        return True


    def azure_authorize(self, username=None, password=None, callback=None):
        """
        Perform multi-step authorization with CBC's azure authorization platform.
        """
        sess = requests.Session()

        if not CBC.azure_authorize_authorize(sess):
            log('Authorization "authorize" step failed', True)
            return False

        cookies = sess.cookies.get_dict()
        if 'x-ms-cpim-csrf' not in cookies:
            log('Unable to get csrt token for self asserted', True)
            return False

        if 'x-ms-cpim-trans' not in cookies:
            log('Unable to get transaction for self asserted', True)
            return False

        trans = cookies['x-ms-cpim-trans']
        trans = b64decode(trans).decode()
        trans = json.loads(trans)
        if not 'C_ID' in trans:
            log('Unable to get C_ID from trans', True)
            return False
        tid = trans['C_ID']

        tid_str = f'{{"TID":"{tid}"}}'.encode()
        b64_tid = b64encode(tid_str).decode('ascii')
        b64_tid = b64_tid.rstrip('=')
        tx_arg = f'StateProperties={b64_tid}'
        csrf_arg = cookies['x-ms-cpim-csrf']

        if not CBC.azure_authorize_self_asserted(sess, username, password, csrf_arg, tx_arg):
            log('Authorization "SelfAsserted" step failed', True)
            return False

        if not CBC.azure_authorize_confirmed(sess, csrf_arg, tx_arg):
            log('Authorization "confirmed" step failed', True)
            return False

        if not CBC.azure_authorize_sign_in(sess, csrf_arg, tx_arg):
            log('Authorization "confirmed" step failed', True)
            return False

        return True

    def authorize(self, username=None, password=None, callback=None):
        """Authorize for video playback."""
        token = self.radius_login(username, password)
        if callback is not None:
            callback(25)
        if token is None:
            log('Radius Login failed', True)
            return False

        jwt = self.radius_jwt(token)
        if callback is not None:
            callback(50)
        if jwt is None:
            log('Radius JWT retrieval failed', True)
            return False

        # token = self.login(login_url, auth['devid'], jwt)
        auth = {}
        token = self.get_access_token(jwt)
        if callback is not None:
            callback(75)
        if token is None:
            log('Access token retrieval failed', True)
            return False
        auth['token'] = token

        claims = self.get_claims_token(token)
        if callback is not None:
            callback(100)
        if token is None:
            log('Claims token retrieval failed', True)
            return False
        auth['claims'] = claims

        saveAuthorization(auth)
        save_cookies(self.session.cookies)

        return True

    def radius_login(self, username, password):
        """Login with Radius using user credentials."""
        query = urllib.parse.urlencode({'apikey': API_KEY})

        data = {
            'email': username,
            'password': password
        }
        url = RADIUS_LOGIN_FMT.format(query)
        req = self.session.post(url, json=data)
        if not req.status_code == 200:
            log('{} returns status {}'.format(req.url, req.status_code), True)
            return None

        token = json.loads(req.content)['access_token']

        return token

    def radius_jwt(self, token):
        """Exchange a radius token for a JWT."""
        query = urllib.parse.urlencode({
            'access_token': token,
            'apikey': API_KEY,
            'jwtapp': 'jwt'
        })
        url = RADIUS_JWT_FMT.format(query)
        req = self.session.get(url)
        if not req.status_code == 200:
            log('{} returns status {}'.format(req.url, req.status_code))
            return None
        return json.loads(req.content)['signature']

    def get_access_token(self, jwt):
        """Exchange a JWT for another JWT."""
        data = {'jwt': jwt}
        req = self.session.post(TOKEN_URL, json=data)
        if not req.status_code == 200:
            log('{} returns status {}'.format(req.url, req.status_code), True)
            return None
        return json.loads(req.content)['accessToken']

    def get_claims_token(self, access_token):
        """Get the claims token for tied to the access token."""
        headers = {'ott-access-token': access_token}
        req = self.session.get(PROFILE_URL, headers=headers)
        if not req.status_code == 200:
            log('{} returns status {}'.format(req.url, req.status_code), True)
            return None
        return json.loads(req.content)['claimsToken']

    def getImage(self, item):
        # ignore 'cbc$liveImage' - the pix don't make sense after the first load
        if 'defaultThumbnailUrl' in item:
            return item['defaultThumbnailUrl']
        if 'cbc$staticImage' in item:
            return item['cbc$staticImage']
        if 'cbc$featureImage' in item:
            return item['cbc$featureImage']
        return None

    @staticmethod
    def get_callsign(item):
        """Get the callsign for a channel."""
        return item[CALLSIGN] if CALLSIGN in item else None

    @staticmethod
    def get_labels(item):
        """Get labels for a CBC item."""
        labels = {
            'studio': 'Canadian Broadcasting Corporation',
            'country': 'Canada'
        }
        if 'cbc$callSign' in item:
            labels['title'] = '{} {}'.format(item['cbc$callSign'], item['title'])
        else:
            labels['title'] = item['title'].encode('utf-8')

        if 'cbc$show' in item:
            labels['tvshowtitle'] = item['cbc$show']
        elif 'clearleap:series' in item:
            labels['tvshowtitle'] = item['clearleap:series']

        if 'description' in item:
            labels['plot'] = item['description'].encode('utf-8')
            labels['plotoutline'] = item['description'].encode('utf-8')

        if 'cbc$liveDisplayCategory' in item:
            labels['genre'] = item['cbc$liveDisplayCategory']
        elif 'media:keywords' in item:
            labels['genre'] = item['media:keywords']

        if 'clearleap:season' in item:
            labels['season'] = item['clearleap:season']

        if 'clearleap:episodeInSeason' in item:
            labels['episode'] = item['clearleap:episodeInSeason']

        if 'media:rating' in item:
            labels['mpaa'] =  item['media:rating']

        if 'premiered' in item:
            labels['premiered'] = item['premiered']

        if 'video' in item:
            labels['mediatype'] = 'video'
        elif 'cbc$audioVideo' in item:
            if item['cbc$audioVideo'].lower() == 'video':
                labels['mediatype'] = 'video'

        return labels


    def parseSmil(self, smil):
        r = self.session.get(smil)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(smil, r.status_code), True)
            return None
        save_cookies(self.session.cookies)

        dom = parseString(r.content)
        seq = dom.getElementsByTagName('seq')[0]
        video = seq.getElementsByTagName('video')[0]
        src = video.attributes['src'].value
        title = video.attributes['title'].value
        abstract = video.attributes['abstract'].value
        return src

    def get_session():
        """Get a requests session object with CBC cookies."""
        sess = requests.Session()
        cookies = loadCookies()
        if cookies is not None:
            sess.cookies = cookies
        return sess
