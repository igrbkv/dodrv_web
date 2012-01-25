#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Заголовок:
    Иконка_Пармы Тип_регистратора Номер П/С
Меню:
    Состояние Настройка Файлы Лог Сервис
Поменю Настройка:
    Регистратор Аналоги Дискреты ОМП Сеть Смена_пароля
    
"""
import web
import session

urls = (
    '/login', 'login.Login',
    '/logout', 'login.Logout',
    '/log', 'log.Log',
    '/config/password', 'login.Password',
    '/config/recorder', 'recorder.Recorder',
    '/config/discretes', 'discretes.Discretes',
    '/config/discretes/(\d+)', 'discretes.Discretes',
    '/config/discrete/(\d+)/(\d+)', 'discrete.Discrete',
    '/config/analogs', 'analogs.Analogs',
    '/config/analogs/(\d+)', 'analogs.Analogs',
    '/config/analog/(\d+)/(\d+)', 'analog.Analog',
    '/config/users', 'users.Users',
    '/state/system', 'state.System',
    '/state/system/pov/(\d+)', 'state.PovStatistic',
    '/state/discretes', 'dstate.DState',
    '/state/discretes/(\d+)', 'dstate.DState',
    '/state/analogs', 'astate.AState',
    '/state/analogs/(\d+)', 'astate.AState',
    '/state/acds/(\d+)', 'astate.ACDState',
    '/state/filters', 'fstate.FState',
    '/state/filters/(\d+)', 'fstate.FState',
    '/files/recorders', 'files.Recorders',
    '/files/recorders/(\d+)', 'files.Recorders',
    '/files/emergencys', 'files.Emergencys',
    '/files/emergencys/(\d+)', 'files.Emergencys',
)


app = web.application(urls, globals())
session.addSessions(app)

if __name__=='__main__': 
    #web.internalerror = web.debugerror
    app.run()

application = app.wsgifunc()
