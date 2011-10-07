# -*- coding: utf-8 -*-
"""
Порядок элементов в меню - обратный
"""
mainMenu = (
    ('Выход', (
        ('', '/logout'),)),
    ('Сервис', (
        ('', '/service'),)),
    ('Лог', ( 
        ('', '/log'),)),
    ('Файлы', ( 
        ('', '/files'),)),
    ('Настройка', (
        ('Смена пароля', '/config/password'),
        ('Пользователи', '/config/users'),
        ('Сеть', '/config/network'), 
        ('ОМП', '/config/omp'),
        ('Дискреты', '/config/discretes'), 
        ('Аналоги', '/config/analogs'), 
        ('Регистратор', '/config/recorder'))),
    ('Состояние', (
        ('Фильтры', '/state/filters'), 
        ('Дискреты', '/state/discretes'), 
        ('Аналоги', '/state/analogs'), 
        ('Система', '/'),)),
)

loginMenu = (
    ('Вход', (
        ('', '/login'),)),
)
