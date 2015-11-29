'''
okru urlresolver plugin
Copyright (C) 2015 DxCx

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
'''

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
import re, os, xbmc, json
import urllib
from urlresolver import common

class Okru(Plugin,UrlResolver,PluginSettings):
    implements=[UrlResolver,PluginSettings]
    name="okru"
    domains=[ "ok.ru" ]
    pattern = '//((?:www\.)?ok\.ru)/videoembed/([0-9]+)'

    def __init__(self):
        p=self.get_setting('priority') or 100
        self.priority=int(p)
        self.net=Net()

    def get_media_url(self,host,media_id):
        full_url=self.get_url(host, media_id)
        url=self.__get_info_url(host,media_id)
        src=self.net.http_GET(url).content
        js=json.loads(src)
        videos=js["videos"]
        opts=[]
        for video in videos:
            opts.append((video["name"], self.__resolve_video(host, video["url"], full_url)))
        return sorted(opts, key=lambda x:x[0])[0][1]

    def __resolve_video(self, host, video_url, url):
        headers = "Origin=http://%s&User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36" % host
        return "%s|%s" % (video_url, headers)

    def __get_info_url(self, host, media_id):
        return "http://%s/dk?cmd=videoPlayerMetadata&mid=%s" % (host, media_id)

    def get_url(self,host,media_id):
        return 'http://%s/videoembed/%s'%(host, media_id)
     
    def get_host_and_id(self, url):
        r = re.search(self.pattern, url)
        if r: return r.groups()
        else: return False
        return('host','media_id')
    
    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.search(self.pattern, url) or 'ok.ru' in host
