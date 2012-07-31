# -*- coding: utf-8 -*-
'''
1. См. также htpasswd.py
2. Администратор - admin, остальные - пользователи
с любыми именами
3. Запрещен доступ к регистратору нескольких admin одновременно.
'''

import web
from web import form
from config import render, SESSIONS_PATH
import session
import syslog
from os import listdir
from htpasswd import htpasswd
from http import nocache


def online(login):
    for f in listdir(SESSIONS_PATH):
        if session.getSession().store[f]['user'] == login:
            return True
    return False


loginForm = form.Form(
    form.Textbox('login', 
        form.Validator('* Значение не задано', bool), 
        description = 'Логин'),
    form.Password('password', description = 'Пароль'),
    form.Button('submit', type = 'submit', html = u'Войти'),
    validators = [form.Validator('Неверная пара логин/пароль',
        lambda i: htpasswd.userValid(str(i.login), str(i.password))),
        form.Validator('Регистратор уже администрируется',
        lambda i: str(i.login) != 'admin' or not online(str(i.login)))]
)


class Login:
    """
    Допустимый логин только один - 'admin'
    Пароль берется из файла PASSWRD_FILE_PATH,
    если файла нет, пароль - 'admin'
    """
    
    title = 'Вход на регистратор'
    
    def POST(self):
        lf = loginForm()
        lf.validates()
        if lf.valid:
            session.setUser(str(lf.login.value))
            syslog.syslog('Подключился ' + str(lf.login.value))
            raise web.seeother('/state/system')
        else:
            lf.password.value = ''
            return render.login(lf, self.title)

    def GET(self):
        web.header('Content-Type', 'text/html; charset= utf-8')
        lf = loginForm()
        return render.login(lf, self.title)

class Logout:
    def GET(self):
        syslog.syslog('Отключился ' + session.getUser())
        session.getSession().kill()
        raise web.seeother('/login')

changePasswordForm = form.Form(
    form.Password('oldPsw', 
        form.Validator('* Неверный пароль', 
            lambda i: htpasswd.userValid(session.getUser(), i)), 
        description = 'Старый пароль', rows = '5'),
    form.Password('newPsw', description = 'Новый пароль'),
    form.Password('secPsw', 
        description = 'Повтор пароля'),
    form.Button('Save', type = 'submit', html = u'Запомнить'),
    validators = [form.Validator('Пароль повторен неверно', lambda i: i.newPsw == i.secPsw)], 
)

class Password:
    """
    FIXME 
    1. Проверка длины пароля?
    """
    title = 'Смена пароля'

    def POST(self):
        cpf = changePasswordForm()
        cpf.validates()
        if cpf.valid:
            un = session.getUser()
            uv = htpasswd.users[un]
            htpasswd.users[un] = (cpf.newPsw.value, uv[1], uv[2])
            htpasswd.save()
            return render.completion(self.title, 'Новый пароль сохранен')
        else:
            cpf.oldPsw.value = ''
            cpf.newPsw.value = ''
            cpf.secPsw.value = ''
            return render.form(cpf, self.title)

    def GET(self):
        nocache()
        
        cpf = changePasswordForm()
        return render.form(cpf, self.title)

class Noaccess:
    def GET(self):
        return render.noaccess('Нет доступа')
