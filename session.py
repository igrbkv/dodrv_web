# -*- coding: utf-8 -*-

import web
from config import SESSIONS_PATH
from os import path, mkdir

def authProcessor(handle):
    """Проверка авторизирован ли пользователь"""
    path = web.ctx.path
    usr = getUser()
    #print usr, path
    if not usr and path != '/login':
        raise web.seeother('/login')
    elif usr != 'admin' and path.startswith('/config') and path != '/config/password':
        raise web.seeother('/noaccess')
    elif usr and path == '/':
        raise web.seeother('/state/system') 
    else:    
        return handle()


def addSessions(app):
    if web.config.get('_session') is None:
        if not path.exists(SESSIONS_PATH):
            mkdir(SESSIONS_PATH)
        store = web.session.DiskStore(SESSIONS_PATH)
        session = web.session.Session(app, store, 
                initializer={'lastPath': None, 'user': None})
        web.config._session = session
        #Добавить процессор авторизации
        app.add_processor(authProcessor)
    else:
        session = web.config._session

def getSession():
    return web.config._session

def setUser(user):
    getSession().user = user

def getUser():
    return getSession().user

def getLastPath():
    return getSession().lastPath

def setLastPath(path):
    getSession().lastPath = path

