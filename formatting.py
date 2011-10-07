# -*- coding: utf-8 -*-

import web
import menu
import config 

"""
class ctx():
    path = '/log'

class web:
    ctx=ctx()

web = web()
"""

def recorderName():
    name = config.xml['name']
    if name:
        return name
    else:
        return 'Регистратор %s' % config.xml['id']

def isCurPath(path):
    return web.ctx.path.split('/')[1] == path.split('/')[1]

def getMenu():
    if web.ctx.path == '/login': 
        return menu.loginMenu
    return menu.mainMenu 

def attrs(d):
    s = ''
    for k, v in d.iteritems():
        if isinstance(v, basestring):
            s += '%s="%s" ' % (k, v)
    return s.strip()

"""
if __name__ == '__main__':
    print getMenu()
"""
