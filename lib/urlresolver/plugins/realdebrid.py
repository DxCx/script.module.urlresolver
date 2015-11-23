"""
urlresolver XBMC Addon
Copyright (C) 2013 t0mm0, JUL1EN094, bstrdsmkr

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import re
import urllib2
import json
import xbmcgui
import xbmc
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import SiteAuth
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common
from t0mm0.common.net import Net

CLIENT_ID = 'MUQMIQX6YWDSU'

class RealDebridResolver(Plugin, UrlResolver, SiteAuth, PluginSettings):
    implements = [UrlResolver, SiteAuth, PluginSettings]
    name = "realdebrid"
    domains = ["*"]

    def __init__(self):
        p = self.get_setting('priority') or 1
        self.priority = int(p)
        self.net = Net()
        self.hosters = None
        self.hosts = None

    def get_media_url(self, host, media_id, retry=False):
        try:
            url = 'https://api.real-debrid.com/rest/1.0/unrestrict/link'
            headers = {'Authorization': 'Bearer %s' % (self.get_setting('token'))}
            data = {'link': media_id}
            result = self.net.http_POST(url, form_data=data, headers=headers).content
        except urllib2.HTTPError as e:
            if not retry and e.code == 401:
                self.refresh_token()
                return self.get_media_url(host, media_id, retry=True)
            else:
                raise UrlResolver.ResolverError('Real Debrid Unrestrict Error: %s' % (e.code))
        except Exception as e:
            raise UrlResolver.ResolverError('Unexpected Exception during RD Unrestrict: %s' % (e))
        else:
            js_result = json.loads(result)
            if 'download' in js_result:
                return js_result['download']
            else:
                raise UrlResolver.ResolverError('No usable link from Real Debrid')
        
    # SiteAuth methods
    def login(self):
        if not self.get_setting('token'):
            self.authorize_resolver()

    def refresh_token(self):
        url = 'https://api.real-debrid.com/oauth/v2/token'
        client_id = self.get_setting('client_id')
        client_secret = self.get_setting('client_secret')
        refresh_token = self.get_setting('refresh')
        data = {'client_id': client_id, 'client_secret': client_secret, 'code': refresh_token, 'grant_type': 'http://oauth.net/grant_type/device/1.0'}
        common.addon.log_debug('Refreshing Expired Real Debrid Token: |%s|%s|' % (client_id, refresh_token))
        try:
            js_result = json.loads(self.net.http_POST(url, data).content)
            common.addon.log_debug('Refreshed Real Debrid Token: |%s|' % (js_result))
            self.set_setting('token', js_result['access_token'])
            self.set_setting('refresh', js_result['refresh_token'])
        except:
            # empty all auth settings to force a re-auth on next use
            self.set_setting('client_id', '')
            self.set_setting('client_secret', '')
            self.set_setting('token', '')
            self.set_setting('refresh', '')
            raise UrlResolver.ResolverError('Unable to Refresh Real Debrid Token')
    
    def authorize_resolver(self):
        url = 'https://api.real-debrid.com/oauth/v2/device/code?client_id=%s&new_credentials=yes' % (CLIENT_ID)
        js_result = json.loads(self.net.http_GET(url).content)
        pd = xbmcgui.DialogProgress()
        line1 = 'Go to URL: %s' % (js_result['verification_url'])
        line2 = 'When prompted enter: %s' % (js_result['user_code'])
        pd.create('URL Resolver Real Debrid Authorization', line1, line2)
        interval = js_result['interval'] * 1000
        device_code = js_result['device_code']
        while True:
            url = 'https://api.real-debrid.com/oauth/v2/device/credentials?client_id=%s&code=%s' % (CLIENT_ID, device_code)
            try:
                js_result = json.loads(self.net.http_GET(url).content)
            except Exception as e:
                common.addon.log_debug('Exception during RD auth: %s' % (e))
                if pd.iscanceled(): return False
            else:
                break
                xbmc.sleep(interval / 2)
                if pd.iscanceled(): return False
                xbmc.sleep(interval / 2)
                if pd.iscanceled(): return False
        pd.close()
        url = 'https://api.real-debrid.com/oauth/v2/token'
        data = {'client_id': js_result['client_id'], 'client_secret': js_result['client_secret'], 'code': device_code, 'grant_type': 'http://oauth.net/grant_type/device/1.0'}
        self.set_setting('client_id', js_result['client_id'])
        self.set_setting('client_secret', js_result['client_secret'])
        common.addon.log_debug('Authorizing Real Debrid: %s' % (js_result['client_id']))
        js_result = json.loads(self.net.http_POST(url, data).content)
        common.addon.log_debug('Authorizing Real Debrid Result: |%s|' % (js_result))
        self.set_setting('token', js_result['access_token'])
        self.set_setting('refresh', js_result['refresh_token'])
        
    def get_url(self, host, media_id):
        return media_id

    def get_host_and_id(self, url):
        return 'www.real-debrid.com', url

    def get_all_hosters(self):
        if self.hosters is None:
            try:
                url = 'https://api.real-debrid.com/rest/1.0/hosts/regex'
                self.hosters = []
                js_result = json.loads(self.net.http_GET(url).content)
                regexes = [regex.lstrip('/').rstrip('/').replace('\/', '/') for regex in js_result]
                self.hosters = [re.compile(regex) for regex in regexes]
            except Exception as e:
                common.addon.log_error('Error getting RD regexes: %s' % (e))
                self.hosters = []
        common.addon.log_debug('RealDebrid hosters : %s' % self.hosters)
        return self.hosters

    def get_hosts(self):
        if self.hosts is None:
            try:
                url = 'https://api.real-debrid.com/rest/1.0/hosts/domains'
                self.hosts = json.loads(self.net.http_GET(url).content)
            except Exception as e:
                common.addon.log_error('Error getting RD hosts: %s' % (e))
                self.hosts = []
        common.addon.log_debug('RealDebrid hosts : %s' % self.hosts)

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        if self.get_setting('authorize') == 'false': return False
        common.addon.log_debug('in valid_url %s : %s' % (url, host))
        if url:
            self.get_all_hosters()
            for host in self.hosters:
                # common.addon.log_debug('RealDebrid checking host : %s' %str(host))
                if re.search(host, url):
                    common.addon.log_debug('RealDebrid Match found')
                    return True
        elif host:
            self.get_hosts()
            if host.startswith('www.'): host = host.replace('www.', '')
            if any(host in item for item in self.hosts):
                return True
        return False

    # PluginSettings methods
    def get_settings_xml(self):
        xml = PluginSettings.get_settings_xml(self)
        xml += '<setting id="%s_authorize" type="bool" label="Ask for Authorization on First Use" default="false"/>\n' % (self.__class__.__name__)
        xml += '<setting id="%s_token" visible="false" type="text" default=""/>\n' % (self.__class__.__name__)
        xml += '<setting id="%s_refresh" visible="false" type="text" default=""/>\n' % (self.__class__.__name__)
        xml += '<setting id="%s_client_id" visible="false" type="text" default=""/>\n' % (self.__class__.__name__)
        xml += '<setting id="%s_client_secret" visible="false" type="text" default=""/>\n' % (self.__class__.__name__)
        return xml

    # to indicate if this is a universal resolver
    def isUniversal(self):
        return True
