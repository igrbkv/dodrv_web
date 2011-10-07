# -*- coding: utf-8 -*-

import web
import utils, formatting
import configxml

CONFIG_XML = 'filters.conf'  #'/etc/dodrv/filters.conf'
PASSWD_FILE_PATH = 'htpasswd'   #'/etc/dodrv/htpasswd'
# очистка сессий при перезапуске
SESSIONS_PATH = '/tmp/sessions'
MAX_USERS = 15

#На время отладки
web.config.debug = True
cache = False

#Таймаут 1 час
web.config.session_parameters['timeout'] = 60*60

globals = utils.getAllFunctions(formatting)

render = web.template.render('templates/', base = 'layout', cache = cache, globals = globals)


xml = configxml.configXml(CONFIG_XML)
xmlRender = web.template.frender('templates/config.xml', globals = globals)

rewriteConfigXml = lambda: utils.rewrite(CONFIG_XML, str(xmlRender(xml)))
