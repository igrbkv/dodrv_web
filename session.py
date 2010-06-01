# -*- coding: utf-8 -*-

import web

def authProcessor(handle):
    """Проверка авторизирован ли пользователь"""
    path = web.ctx.path
    if not isLogged() and path != '/login':
        raise web.seeother('/login')
    else:
        return handle()


def addSessions(app):
    if web.config.get('_session') is None:
        store = web.session.DiskStore('sessions')
        session = web.session.Session(app, store, 
                initializer={'isLogged' : False, 'lastPath': None})
        web.config._session = session
        #Добавить процессор авторизации
        app.add_processor(authProcessor)
    else:
        session = web.config._session

def getSession():
    return web.config._session

def isLogged():
    return getSession().isLogged

def setLogged(res = True):
    getSession().isLogged = res

def getLastPath():
    return getSession().lastPath

def setLastPath(path):
    getSession().lastPath = path

