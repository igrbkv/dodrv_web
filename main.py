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
import login, index


urls = (
    '/', 'index.Index',
    '/login', 'login.Login',
    '/config/password', 'login.Password',
    '/config/recorder', 'recorder.Recorder',
    '/config/discretes/(\d+)', 'discretes.Discretes',
    '/config/discrete/(\d+)/(\d+)', 'discrete.Discrete',
    '/config/analogs/(\d+)', 'analogs.Analogs',
    '/config/analog/(\d+)/(\d+)', 'analog.Analog',
)


if __name__=='__main__': 
    app = web.application(urls, globals())
    session.addSessions(app)
    #web.internalerror = web.debugerror
    app.run()

