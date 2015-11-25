'''
Animebam urlresolver plugin
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
from urlresolver import common

class AnimebamResolver(Plugin,UrlResolver,PluginSettings):
    implements=[UrlResolver,PluginSettings]
    name="animebam"
    domains=[ "animebam.com" ]

    def __init__(self):
        p=self.get_setting('priority') or 100
        self.priority=int(p)
        self.net=Net()

    def get_media_url(self,host,media_id):
        url=self.get_url1st(host,media_id)
        headers={'User-Agent':common.IE_USER_AGENT,'Referer':url}
        html=self.net.http_GET(url,headers=headers).content
        video_url = self.__get_best_source(html)
        if not video_url:
            raise UrlResolver.ResolverError('could not find video')
        return self.__resolve_video(video_url, url)

    def __resolve_video(self, video_url, url):
        headers={'Referer':url}
        return self.net.http_HEAD(video_url, headers=headers).get_url()

    def __get_best_source(self, html):
        mirrorlist = []
        r=re.search('sources:\s*\[\{(.+)\}\]', html, re.DOTALL)
        if not r:
            return None

        mirrors=re.findall('file:\s"(.+?)",\slabel:\s"(.+?)"', r.group(1), re.DOTALL)
        mirrorlist = [(i[1], i[0]) for i in mirrors]
        # TODO: in the future return all.
        return sorted(mirrorlist, key=lambda k: k[0])[0][1]

    def get_url(self,host,media_id):
        return 'http://%s/%s'%(host, media_id)

    def get_url1st(self,host,media_id):
        return 'http://%s/embed/%s'%(host, media_id)

    def get_host_and_id(self, url):
        r=re.search('//(?:www\.)?(animebam.com)/(?:embed\/)?([0-9a-zA-Z]+)',url)
        if r: return r.groups()
        else: return False
        return('host','media_id')

    def valid_url(self,url,host):
        if self.get_setting('enabled')=='false': return False
        return (re.match('http://(?:www.)?(animebam.com)/(?:embed\/)?([0-9A-Za-z]+)',url) or 'animebam' in host)

