# -*- coding: utf-8 -*-
"""
Порядок элементов в меню - обратный
"""
mainMenu = (
    ('Выход', (
        ('', '/logout'),)),
    ('Лог', ( 
        ('', '/log'),)),
    ('Файлы', ( 
        ('Самописцы', '/files/recorders'),
        ('Аварии', '/files/emergencys'),)),
    ('Настройка', (
        ('Сервис', '/config/service'),
        ('Смена пароля', '/config/password'),
        ('Пользователи', '/config/users'),
        ('Время', '/config/time'), 
        ('Сеть', '/config/network'), 
        ('Дискреты', '/config/discretes'), 
        ('Аналоги', '/config/analogs'), 
        ('Регистратор', '/config/recorder'))),
    ('Состояние', (
        ('Синхронизация', '/state/syncronization'), 
        ('Сеть', '/state/network'), 
        ('Фильтры', '/state/filters'), 
        ('Дискреты', '/state/discretes'), 
        ('Аналоги', '/state/analogs'), 
        ('Система', '/state/system'),)),
)

loginMenu = (
    ('Вход', (
        ('', '/login'),)),
)
