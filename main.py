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
    '/', 'state.System',
    '/login', 'login.Login',
    '/logout', 'login.Logout',
    '/config/password', 'login.Password',
    '/config/recorder', 'recorder.Recorder',
    '/config/discretes/(\d+)', 'discretes.Discretes',
    '/config/discretes', 'discretes.PreDiscretes',
    '/config/discrete/(\d+)/(\d+)', 'discrete.Discrete',
    '/config/analogs/(\d+)', 'analogs.Analogs',
    '/config/analogs', 'analogs.PreAnalogs',
    '/config/analog/(\d+)/(\d+)', 'analog.Analog',
    '/config/users', 'users.Users',
)


app = web.application(urls, globals())
session.addSessions(app)

if __name__=='__main__': 
    #web.internalerror = web.debugerror
    app.run()

application = app.wsgifunc()
