"""
    OVERALL CREDIT TO:
        t0mm0, Eldorado, VOINAGE, BSTRDMKR, tknorris, smokdpi, TheHighway

    urlresolver XBMC Addon
    Copyright (C) 2011 t0mm0

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
import json
import urllib
from t0mm0.common.net import Net
from urlresolver import common
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin

class MailRuResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "mail.ru"
    domains = ["mail.ru"]
    pattern = '//((?:videoapi.)?my\.mail\.ru)/+(?:videos/+embed/+)?([^/]+)/+([^/]+)/+(?:video/+)?(?:[^/]+)/+([a-zA-Z1-9]+)'

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        web_url = re.findall("<a href=\"(.+?)\"", self.net.http_GET(web_url).content)[0]
        headers={'Referer':web_url}
        html = self.net.http_GET(web_url, headers=headers).content
        match = re.search('"metaUrl"\s*:\s*"([^"]+)', html)
        videos = []
        if match:
            json_url = match.group(1)
            response = self.net.http_GET(json_url)
            html = response.content
            if html:
                js_data = json.loads(html)
                headers = dict(response._response.info().items())
                stream_url = ''
                best_quality = 0
                for video in js_data['videos']:
                    video_headers={}
                    if 'set-cookie' in headers:
                        cookie_key=re.findall("(video_key=[^;]+);", headers['set-cookie'])[0]
                        video_headers['Cookie'] = cookie_key
                    quality = video['key']
                    video_url = "%s|%s" % (video['url'], urllib.urlencode(video_headers))
                    videos.append((quality, video_url))

        if not len(videos):
            raise UrlResolver.ResolverError('No playable video found.')

        return sorted(videos, key=lambda x: x[0])[0][1]

    def get_url(self, host, media_id):
        mtype, user, media_id = media_id.split('|')
        return 'http://videoapi.my.mail.ru/videos/embed/%s/%s/st/%s.html' % (mtype, user, media_id)

    def get_host_and_id(self, url):
        r = re.search(self.pattern, url)
        if r:
            host, mtype, user, media_id = r.groups()
            return host, '%s|%s|%s' % (mtype, user, media_id)
        else:
            return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.search(self.pattern, url) or 'mail.ru' in host
