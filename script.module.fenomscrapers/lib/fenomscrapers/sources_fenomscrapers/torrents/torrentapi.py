# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 10-05-2020)

'''
    Fenomscrapers Project
'''

import json
import re
import time

try: from urlparse import parse_qs
except ImportError: from urllib.parse import parse_qs
try: from urllib import urlencode, quote_plus, unquote_plus
except ImportError: from urllib.parse import urlencode, quote_plus, unquote_plus

from fenomscrapers.modules import cache
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 3
		self.language = ['en']
		self.base_link = 'https://torrentapi.org' #-just to satisfy scraper_test
		self.tvsearch = 'https://torrentapi.org/pubapi_v2.php?app_id=Torapi&token={0}&mode=search&search_string={1}&ranked=0&limit=100&format=json_extended'
		self.tvshowearch = 'https://torrentapi.org/pubapi_v2.php?app_id=Torapi&token={0}&mode=search&search_tvdb={1}&ranked=0&limit=100&format=json_extended' #thinking more on using this
		self.msearch = 'https://torrentapi.org/pubapi_v2.php?app_id=Torapi&token={0}&mode=search&search_imdb={1}&ranked=0&limit=100&format=json_extended'
		self.token = 'https://torrentapi.org/pubapi_v2.php?app_id=Torapi&get_token=get_token'
		self.key = cache.get(self._get_token, 0.2) # 800 secs token is valid for
		self.min_seeders = 1
		self.pack_capable = True


	def _get_token(self):
		token = client.request(self.token)
		token = json.loads(token)["token"]
		return token


	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			url = parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urlencode(url)
			return url
		except:
			return


	def sources(self, url, hostDict):
		sources = []
		try:
			if not url: return sources

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']

			query = '%s %s' % (title, hdlr)
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', query)

			if 'tvshowtitle' in data:
				search_link = self.tvsearch.format(self.key, quote_plus(query))
			else:
				search_link = self.msearch.format(self.key, data['imdb'])
			# log_utils.log('search_link = %s' % search_link, log_utils.LOGDEBUG)

			time.sleep(2.1)
			rjson = client.request(search_link, error=True)
			if not rjson or not 'torrent_results' in str(rjson):
				return sources

			files = json.loads(rjson)['torrent_results']

			for file in files:
				url = file["download"]
				url = url.split('&tr')[0]
				hash = re.compile('btih:(.*?)&').findall(url)[0]

				name = file["title"]
				name = unquote_plus(name)
				name = source_utils.clean_name(title, name)
				if source_utils.remove_lang(name, episode_title):
					continue

				if not source_utils.check_title(title, aliases, name, hdlr, data['year']):
					continue

				# filter for episode multi packs (ex. S01E01-E17 is also returned in query)
				if episode_title:
					if not source_utils.filter_single_episodes(hdlr, name):
						continue

				try:
					seeders = int(file["seeders"])
					if self.min_seeders > seeders: 
						continue
				except:
					seeders = 0
					pass

				quality, info = source_utils.get_release_quality(name, name)
				try:
					dsize, isize = source_utils.convert_size(file["size"], to='GB')
					info.insert(0, isize)
				except:
					dsize = 0
					pass
				info = ' | '.join(info)

				sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
										'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			return sources
		except:
			source_utils.scraper_error('TORRENTAPI')
			return sources


	def sources_packs(self, url, hostDict, search_series=False, total_seasons=None, bypass_filter=False):
		sources = []
		self.bypass_filter = bypass_filter

		if search_series: # torrentapi does not have showPacks
			return sources
		try:
			if not url: return sources

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'].replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.year = data['year']
			self.season_x = data['season']
			self.season_xx = self.season_x.zfill(2)

			query = re.sub('[^A-Za-z0-9\s\.-]+', '', self.title)
			search_link = self.tvsearch.format(self.key, quote_plus(query + ' S%s' % self.season_xx))
			# log_utils.log('search_link = %s' % str(search_link), __name__, log_utils.LOGDEBUG)

			time.sleep(2.1)
			rjson = client.request(search_link, error=True)
			if not rjson or not 'torrent_results' in str(rjson):
				return sources

			files = json.loads(rjson)['torrent_results']
			for file in files:
				url = file["download"]
				url = url.split('&tr')[0]
				hash = re.compile('btih:(.*?)&').findall(url)[0]

				name = file["title"]
				name = unquote_plus(name)
				name = source_utils.clean_name(self.title, name)
				if source_utils.remove_lang(name):
					continue

				if not self.bypass_filter:
					if not source_utils.filter_season_pack(self.title, self.aliases, self.year, self.season_x, name):
						continue
				package = 'season'

				try:
					seeders = int(file["seeders"])
					if self.min_seeders > seeders: 
						continue
				except:
					seeders = 0
					pass

				quality, info = source_utils.get_release_quality(name, name)
				try:
					dsize, isize = source_utils.convert_size(file["size"], to='GB')
					info.insert(0, isize)
				except:
					dsize = 0
					pass
				info = ' | '.join(info)

				sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
										'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package})
			return sources
		except:
			source_utils.scraper_error('TORRENTAPI')
			return sources


	def resolve(self, url):
		return url