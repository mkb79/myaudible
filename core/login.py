import base64
import json
import re
import secrets
import uuid
from urllib.parse import parse_qs

import httpx
from django.utils import timezone
from typing import Dict, Optional, Tuple

from .marketplaces import Marketplace


USER_AGENT = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
)


def build_device_serial() -> str:
    return uuid.uuid4().hex.upper()


def build_client_id(serial: str) -> str:
    client_id = serial.encode() + b'#A2CZJZGLK2JJVM'
    return client_id.hex()


def build_init_cookies() -> Dict[str, str]:
    """Build initial cookies to prevent captcha in most cases."""
    frc = secrets.token_bytes(313)
    frc = base64.b64encode(frc).decode('ascii').rstrip('=')

    map_md = {
        'device_user_dictionary': [],
        'device_registration_data': {
            'software_version': '35602678'
        },
        'app_identifier': {
            'app_version': '3.56.2',
            'bundle_id': 'com.audible.iphone'
        }
    }
    map_md = json.dumps(map_md)
    map_md = base64.b64encode(map_md.encode()).decode().rstrip('=')

    amzn_app_id = 'MAPiOSLib/6.0/ToHideRetailLink'

    return {'frc': frc, 'map-md': map_md, 'amzn-app-id': amzn_app_id}


def build_oauth_url(
    country_code: str,
    domain: str,
    market_place_id: str,
    client_id: str,
    with_username: bool = False
) -> Tuple[str, str]:
    """Builds the url to login to Amazon as an Audible device"""

    base_url = f'https://www.amazon.{domain}/ap/signin'
    return_to = f'https://www.amazon.{domain}/ap/maplanding'
    assoc_handle = f'amzn_audible_ios_{country_code}'
    page_id = 'amzn_audible_ios'

    if with_username:
        if country_code.lower() not in ('de', 'us', 'uk'):
            raise ValueError(
                'Login with username is only supported for DE, US '
                'and UK marketplaces!'
            )

        base_url = f'https://www.audible.{domain}/ap/signin'
        return_to = f'https://www.audible.{domain}/ap/maplanding'
        assoc_handle = f'amzn_audible_ios_lap_{country_code}'
        page_id = 'amzn_audible_ios_privatepool'

    oauth_params = {
        'openid.oa2.response_type': 'token',
        'openid.return_to': return_to,
        'openid.assoc_handle': assoc_handle,
        'openid.identity': (
            'http://specs.openid.net/auth/2.0/identifier_select'
        ),
        'pageId': page_id,
        'accountStatusPolicy': 'P1',
        'openid.claimed_id': (
            'http://specs.openid.net/auth/2.0/identifier_select'
        ),
        'openid.mode': 'checkid_setup',
        'openid.ns.oa2': 'http://www.amazon.com/ap/ext/oauth/2',
        'openid.oa2.client_id': f'device:{client_id}',
        'openid.ns.pape': 'http://specs.openid.net/extensions/pape/1.0',
        'marketPlaceId': market_place_id,
        'openid.oa2.scope': 'device_auth_access',
        'forceMobileLayout': 'true',
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.pape.max_auth_age': '0'
    }

    return httpx.URL(base_url, params=oauth_params)


class DjangoAudibleLogin:
    def __init__(
        self,
        country_code: str,
        serial: Optional[str] = None,
        with_username: bool = False
    ) -> None:
        self._with_username = with_username
        self._marketplace = Marketplace.from_country_code(country_code)
        self._serial = serial or build_device_serial()
        self._session: Optional[httpx.AsyncClient] = None
        self._start_url: httpx.URL = self.build_start_url()
        self._access_token: Optional[str] = None
        self._last_request: Optional[httpx.Request] = None
        self._last_response: Optional[httpx.Response] = None
        self._proxy_abs_url = None

    def build_start_url(self):
        return build_oauth_url(
            country_code=self._marketplace.country_code,
            domain=self._marketplace.domain,
            market_place_id=self._marketplace.market_place_id,
            client_id=build_client_id(serial=self._serial),
            with_username=self._with_username
        )

    def create_session(self):
        default_headers = {
            'User-Agent': USER_AGENT,
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip'
        }
        init_cookies = build_init_cookies()
        base_url = self._start_url.scheme + '://' + self._start_url.host
        self._session = httpx.Client(
            headers=default_headers,
            cookies=init_cookies,
            base_url= base_url
        )

    def request(self, method, url, **kwargs):
        response = self._session.request(method, url, **kwargs)

        self._last_response = response
        self._last_request = response.request
        self._last_response_content = self._last_response.content

        if 'text/html' in response.headers['Content-Type']:
            self._last_response_content = self.rewrite_html()
        
        if b'openid.oa2.access_token' in self._last_request.url.query:
            parsed_url = parse_qs(self._last_request.url.query.decode())
            access_token = parsed_url['openid.oa2.access_token'][0]
            self._access_token = access_token

    def rewrite_html(self):
        base_url = self._start_url.scheme + '://' + self._start_url.host
        reserve_byte = httpx.URL(self._proxy_abs_url).raw_path.decode()
        abs_uri2 = self._proxy_abs_url
        abs_uri2 += self._last_response.url.raw_path.decode().lstrip('/')

        response = self._last_response.text

        # rewrite urls without scheme
        response = re.sub(
            r'''((?:src|style)=['|"]?)(//)''', r'\1'
            + 'https:' + r'\2', response, flags=re.IGNORECASE
        )

        # make relative url to absolute with base_url
        response = re.sub(
            r'''((?:src|style)=['|"]?)(/)''', r'\1'
            + base_url + r'\2', response, flags=re.IGNORECASE
        )

        # insert proxy url at the beginning of relative urls
        response = re.sub(
            r'''((?:href|action|data-refresh-url)=['|"]?)(/)''', r'\1'
            + reserve_byte + r'\2', response, flags=re.IGNORECASE
        )

        # rewrite absolute urls
        response = re.sub(
            r'''((?:href|action)=['|"]?)(''' + base_url + r''')(.*)''', r'\1'
            + reserve_byte + r'\3', response, flags=re.IGNORECASE
        )

        response = re.sub('/ap/uedata', base_url + '/ap/uedata',
                          response, flags=re.IGNORECASE)

        return response

    def register(self):
        if not self.state.status_name == 'COMPLETE':
            raise Exception('Login not completed')

        body = {
            "requested_token_type": [
                "bearer", "mac_dms", "website_cookies",
                "store_authentication_cookie"
             ],
            "cookies": {
                "website_cookies": [],
                "domain": f".amazon.{self._marketplace.domain}"
            },
            "registration_data": {
                "domain": "Device",
                "app_version": "3.26.1",
                "device_serial": self._serial,
                "device_type": "A2CZJZGLK2JJVM",
                "device_name": (
                    "%FIRST_NAME%%FIRST_NAME_POSSESSIVE_STRING%%DUPE_"
                    "STRATEGY_1ST%Audible for iPhone"
                ),
                "os_version": "14.7.0",
                "device_model": "iPhone",
                "app_name": "Audible"
            },
            "auth_data": {"access_token": self._access_token},
            "requested_extensions": ["device_info", "customer_info"]
        }
    
        resp = httpx.post(f"https://api.amazon.{self._marketplace.domain}/auth/register", json=body)
        return resp


class SessionObject:
    def __init__(self, session_key, expires_in, session):
        self._session_key = session_key
        self._session_uuid = uuid.uuid4()
        self._expires_at = timezone.now() + timezone.timedelta(seconds=expires_in)
        self._session = session

    @property
    def session_key(self):
        return self._session_key

    @property
    def session_uuid(self):
        return self._session_uuid

    @property
    def session(self):
        return self._session

    @property
    def expires_at(self):
        return self._expires_at

    @property
    def is_expired(self):
        return self._expires_at >= timezone.now()

    def close_session(self):
        self.session._session.close()

    def start_session(self, proxy_url):
        self.session.create_session()
        self.session._proxy_abs_url = proxy_url
        self.session.request('GET', self.session._start_url)

    @property
    def is_logged_in(self):
        return self.session._access_token is not None


class AudibleLoginSessionPool:
    def __init__(self):
        self._running_sessions = {}

    def create_session(self, session_key, expires_in=300, **kwargs):
        if self.has_session(session_key):
            raise Exception('Login session exists')

        session = DjangoAudibleLogin(**kwargs)
        session_obj = SessionObject(
            session_key=session_key,
            expires_in=expires_in,
            session=session)
        self._running_sessions[session_key] = session_obj

        return session_obj

    def has_session(self, session_key):
        return session_key in self._running_sessions

    def has_uuid(self, session_uuid):
        for session_obj in self._running_sessions.values():
            if session_uuid == session_obj.session_uuid:
                return True
        return False

    def get_session(self, session_key):
        try:
            return self._running_sessions[session_key]
        except KeyError:
            pass

    def get_session_by_uuid(self, session_uuid):
        for session_obj in self._running_sessions.values():
            if session_uuid == session_obj.session_uuid:
                return session_obj

    def get_uuid_for_session_key(self, session_key):
        try:
            return self._running_sessions[session_key].session_uuid
        except KeyError:
            pass

    def remove_session(self, session_key):
        try:
           self._running_sessions[session_key].close_session()
           del self._running_sessions[session_key]
        except KeyError:
            pass

    def cleanup_sessions(self):
        remove_sessions = []
        for session_id, session_obj in self._running_sessions.items():
            if session_obj.is_expired:
                remove_sessions.append(session_id)

        for i in remove_sessions:
            self.remove_session(i)


session_pool = AudibleLoginSessionPool()
