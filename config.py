# -*- coding: utf-8 -*-

import web
import utils, formatting
import configxml

DEBUG_PATH = 'debug'

CONFIG_XML = DEBUG_PATH + '/etc/dodrv/filters.conf'
PASSWD_FILE_PATH = DEBUG_PATH + '/etc/dodrv/htpasswd'
# очистка сессий при перезапуске
SESSIONS_PATH = '/tmp/sessions'
FILTERS = 'filters'

MAX_USERS = 15

MAX_POV = 6

POV_STAT = DEBUG_PATH + '/proc/driver/pov'

LOG_PATH = DEBUG_PATH + '/var/log/everything'

FILES_IN_PAGE = 20

# Файлы аварий
EMERGENCY_PATH = DEBUG_PATH + '/dodrv/emergency'
# Файлы самописца 
RECORDER_PATH = DEBUG_PATH + '/dodrv/recorder'

#для utils.getPages 
PAGES_AROUND = 5

#На время отладки
if DEBUG_PATH:
    web.config.debug = True
    cache = False

#Таймаут 1 час
web.config.session_parameters['timeout'] = 60*60

globals = utils.getAllFunctions(formatting)

render = web.template.render('templates/', base = 'layout', cache = cache, globals = globals)


xml = configxml.configXml(CONFIG_XML)
xmlRender = web.template.frender('templates/config.xml', globals = globals)

rewriteConfigXml = lambda: utils.rewrite(CONFIG_XML, str(xmlRender(xml)))
