"""
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
from t0mm0.common.net import Net
from urlresolver import common
from urlresolver.plugnplay.interfaces import GenericUrlResolver, UrlResolver, PluginSettings
from urlresolver.plugnplay import Plugin

class Mp4uploadResolver(Plugin, GenericUrlResolver):
    implements = [UrlResolver, PluginSettings]
    name = "mp4upload"
    domains = ["mp4upload.com"]
    pattern='//(?:www\.)?(mp4upload.com)/embed-(.+?)\.'
    url_template = 'http://%(host)s/embed-%(media_id)s.html'

    def __init__(self):
        GenericUrlResolver.__init__(self)

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        link = self.net.http_GET(web_url).content
        link = ''.join(link.splitlines()).replace('\t', '')
        r = re.search('\'file\': \'(.+?)\'', link)
        if not r:
            raise UrlResolver.ResolverError('could not find video')

        return r.groups(1)[0]
