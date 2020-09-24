# -*- coding: utf-8 -*-

from sys import argv
try:
	from urlparse import parse_qsl
except:
	from urllib.parse import parse_qsl

from fenomscrapers import sources_fenomscrapers
from fenomscrapers.modules import control

params = dict(parse_qsl(argv[2].replace('?', '')))
action = params.get('action')
mode = params.get('mode')
query = params.get('query')
name = params.get('name')


if action is None:
	control.openSettings('0.0', 'script.module.fenomscrapers')


if action == "FenomScrapersSettings":
	control.openSettings('0.0', 'script.module.fenomscrapers')


elif mode == "FenomScrapersSettings":
	control.openSettings('0.0', 'script.module.fenomscrapers')


elif action == 'ShowChangelog':
	from fenomscrapers.modules import changelog
	changelog.get()


elif action == 'ShowHelp':
	from fenomscrapers.help import help
	help.get(name)


elif action == "Defaults":
	sourceList = []
	sourceList = sources_fenomscrapers.all_providers
	for i in sourceList:
		source_setting = 'provider.' + i
		value = control.getSettingDefault(source_setting)
		control.setSetting(source_setting, value)


elif action == "toggleAll":
	sourceList = []
	sourceList = sources_fenomscrapers.all_providers
	for i in sourceList:
		source_setting = 'provider.' + i
		control.setSetting(source_setting, params['setting'])


elif action == "toggleAllHosters":
	sourceList = []
	sourceList = sources_fenomscrapers.hoster_providers
	for i in sourceList:
		source_setting = 'provider.' + i
		control.setSetting(source_setting, params['setting'])


elif action == "toggleAllTorrent":
	sourceList = []
	sourceList = sources_fenomscrapers.torrent_providers
	for i in sourceList:
		source_setting = 'provider.' + i
		control.setSetting(source_setting, params['setting'])


elif action == "toggleAllPackTorrent":
	sourceList = []
	from fenomscrapers import pack_sources
	sourceList = pack_sources()
	for i in sourceList:
		source_setting = 'provider.' + i
		control.setSetting(source_setting, params['setting'])

elif action == 'openMyAccount':
	control.openSettings('0.0', 'script.module.myaccounts')
	control.sleep(100)
	while control.condVisibility('Window.IsVisible(addonsettings)'):
		control.sleep(100)
	control.syncMyAccounts()
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'script.module.fenomscrapers')

elif action == 'syncMyAccount':
	control.syncMyAccounts()
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'script.module.fenomscrapers')