# -*- coding: utf-8 -*-

import web
import utils, formatting
import configxml

CONFIG_XML = 'config.xml'
PASSWD_FILE_PATH = 'password'
MASTER_KEY = '2128506'

#На время отладки
web.config.debug = True
cache = False

#Таймаут 24 час
web.config.session_parameters['timeout'] = 60*60*24

globals = utils.getAllFunctions(formatting)

render = web.template.render('templates/', base = 'layout', cache = cache, globals = globals)


xml = configxml.configXml(CONFIG_XML)
xmlRender = web.template.frender('templates/config.xml', globals = globals)

