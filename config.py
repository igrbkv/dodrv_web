# -*- coding: utf-8 -*-

import web
import utils, formatting
import configxml

CONFIG_XML = 'filters.conf'  #'/etc/dodrv/filters.conf'
PASSWD_FILE_PATH = 'htpasswd'   #'/etc/dodrv/htpasswd'
# очистка сессий при перезапуске
SESSIONS_PATH = '/tmp/sessions'

MAX_USERS = 15

MAX_POV = 6

#POV_STAT = '/proc/driver/pov'
POV_STAT = 'cat_driver_proc.txt'

#LOG_PATH = '/var/log/everything'
LOG_PATH = '/home/igor/tmp'

FILES_IN_PAGE = 20

# Файлы аварий
#EMERGENCY_PATH = '/dodrv/emergency'
EMERGENCY_PATH = '/home/igor/workspace/dodrv/tests/emergency'   
# Файлы самописца 
#RECORDER_PATH = '/dodrv/recorder'
RECORDER_PATH = '/home/igor/workspace/dodrv/tests/recorder'   

#для utils.getPages 
PAGES_AROUND = 5

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
