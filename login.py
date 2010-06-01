# -*- coding: utf-8 -*-

import web
from web import form
from config import render, PASSWD_FILE_PATH, MASTER_KEY
import session


def readPassword():
    psw = 'admin'
    try:
        with open(PASSWD_FILE_PATH, 'r') as f:
            psw = f.read()
    except:
        pass
    return psw

def writePassword(psw):
    ret = True
    try:
        with open(PASSWD_FILE_PATH, 'w') as f:
            f.write(psw)
    except:
        ret = False
    return ret

loginForm = form.Form(
    form.Textbox('login', 
        form.Validator('* Значение не задано', bool), 
        description = 'Логин'),
    form.Password('password', description = 'Пароль'),
    form.Button('Войти', type = 'submit'),
)

class Login:
    """
    Допустимый логин только один - 'admin'
    Пароль берется из файла PASSWRD_FILE_PATH,
    если файла нет, пароль - 'admin'
    Мастер-пароль - '2128506'
    """
    title = 'Вход на регистратор'

    def POST(self):
        lf = loginForm()
        lf.validates()
        print lf.login.value, lf.password.value
        if (lf.login.value == 'admin' and lf.password.value == readPassword()) or lf.password.value == MASTER_KEY:
            session.setLogged()
            raise web.seeother('/')
            #eturn render.index('Igor')
        else:
            lf.login.value = ''
            lf.password.value = ''
            if lf.valid:
                lf.note = 'Неверная пара логин/пароль'
            return render.login(lf, self.title)

    def GET(self):
        web.header('Content-Type', 'text/html; charset= utf-8')
        lf = loginForm()
        return render.login(lf, self.title)

changePasswordForm = form.Form(
    form.Password('oldPsw', 
        form.Validator('* Неверный пароль', 
            lambda i: i == readPassword() or i == MASTER_KEY), 
        description = 'Старый пароль', rows = '5'),
    form.Password('newPsw', description = 'Новый пароль'),
    form.Password('secPsw', 
        description = 'Повтор пароля'),
    form.Button('Запомнить', type = 'submit'),
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
            writePassword(cpf.newPsw.value)
            return render.completion(self.title, 'Новый пароль сохранен')
        else:
            cpf.oldPsw.value = ''
            cpf.newPsw.value = ''
            cpf.secPsw.value = ''
            return render.form(cpf, self.title)

    def GET(self):
        web.header('Content-Type', 'text/html; charset= utf-8')
        cpf = changePasswordForm()
        return render.form(cpf, self.title)
