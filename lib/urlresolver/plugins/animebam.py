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

from urlresolver.plugnplay import Plugin
from urlresolver.plugnplay.interfaces import GenericUrlResolver, UrlResolver, PluginSettings
from urlresolver import common
import re

class AnimebamResolver(Plugin, GenericUrlResolver):
    implements=[UrlResolver, PluginSettings]
    name="animebam"
    domains=[ "animebam.com" ]
    pattern='//(?:www\.)?(animebam.com)/(?:embed\/)?([0-9a-zA-Z]+)'
    url_template = 'http://%(host)s/embed/%(media_id)s'

    def __init__(self):
        GenericUrlResolver.__init__(self)

    def get_media_url(self,host,media_id):
        url=self.get_url(host,media_id)
        headers={'User-Agent':common.IE_USER_AGENT,'Referer':url}
        html=self.net.http_GET(url,headers=headers).content
        videos = self.__get_videos(html, url)
        if not len(videos):
            raise UrlResolver.ResolverError('could not find video')

        return sorted(videos, key=lambda k: k[0])[0][1]

    def _resolve(self, video_url, refer):
        headers={'Referer':refer}
        return self.net.http_HEAD(video_url, headers=headers).get_url()

    def __get_videos(self, html, refer):
        mirrorlist = []
        r=re.search('sources:\s*\[\{(.+)\}\]', html, re.DOTALL)
        if not r:
            return None

        mirrors=re.findall('file:\s"(.+?)",\slabel:\s"(.+?)"', r.group(1), re.DOTALL)
        return [(i[1], self._resolve(i[0], refer)) for i in mirrors]
