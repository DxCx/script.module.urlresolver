'''
myviru urlresolver plugin
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

class MyViRuResolver(Plugin,UrlResolver,PluginSettings):
    implements=[UrlResolver,PluginSettings]
    name="myviru"
    domains=[ "myvi.ru" ]
    pattern = '//((?:www\.)?myvi\.ru)/player/embed/html/([0-9a-zA-Z\-_]+)'

    def __init__(self):
        p=self.get_setting('priority') or 100
        self.priority=int(p)
        self.net=Net()

    def get_media_url(self,host,media_id):
        full_url=self.get_url(host, media_id)
        src=self.net.http_GET(full_url).content
        p=re.findall("dataUrl:'([^']+)'",src)[0]
        js=json.loads(self.net.http_GET("http://%s%s" % (host, p)).content)
        videos=js["sprutoData"]["playlist"]
        opts=[]
        for video in videos:
            opts.append((video["title"], self.__resolve_url(video["video"][0]["url"], full_url)))
        return sorted(opts, key=lambda x:x[0])[0][1]

    def __resolve_url(self, url, ref_url):
        headers={'Referer':ref_url}
        return self.net.http_HEAD(url, headers=headers).get_url()

    def get_url(self,host,media_id):
        return 'http://%s/player/embed/html/%s'%(host, media_id)
     
    def get_host_and_id(self, url):
        r = re.search(self.pattern, url)
        if r: return r.groups()
        else: return False
        return('host','media_id')
    
    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.search(self.pattern, url) or 'myvi.ru' in host
