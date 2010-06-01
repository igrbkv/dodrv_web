# -*- coding: utf-8 -*-
"""
Порядок элементов в меню - обратный
"""
mainMenu = (
    ('Сервис', (
        ('', '/service'),)),
    ('Лог', ( 
        ('', '/log'),)),
    ('Файлы', ( 
        ('', '/files'),)),
    ('Настройка', (
        ('Смена пароля', '/config/password'),
        ('Сеть', '/config/network'), 
        ('ОМП', '/config/omp'),
        ('Дискреты', '/config/discretes/0'), 
        ('Аналоги', '/config/analogs/0'), 
        ('Регистратор', '/config/recorder'))),
    ('Состояние', (
        ('', '/'),)),
)

loginMenu = (
    ('Вход', (
        ('', '/login'),)),
)
