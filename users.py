# -*- coding: utf-8 -*-
'''
Добавление и редактирование юзеров.
Максимальное число юзеров ограничено MAX_USERS.
Максимальная длина логина и пароля - 8 символов из латиницы, цифр и подчеркивания.
Максимальная длина строки с допп. информацией - 30 символов.
'''

import web
from web import form
from config import render, MAX_USERS
from htpasswd import htpasswd

REGEXP = '^[0-9a-zA-Z_]*$'

def createUserForm(name, psw, info):
    uf = form.Form(
        form.Checkbox(name + '_del', value = 'value', checked = False),
        form.Hidden(name),
        form.Textbox(name + '_psw', 
            form.Validator('* Длина пароля не должна превышать 8 символов', lambda i: len(i) <= 8),
            form.regexp(REGEXP, '* Недопустимые символы в пароле'),
            value = psw),
        form.Textbox(name + '_info', 
            form.Validator('* Длина информационного поля не должна превышать 30 символов', lambda i: len(i) <= 30 ),
             value = info))
    return uf

def createUsers():
    d = {}
    for k, v in htpasswd.users.iteritems():
        if k != 'admin':
            d[k] = createUserForm(k, v[0], v[2])
    return d

newUserForm = form.Form(
    form.Textbox('new_user',
        form.Validator('* Длина имени не должна превышать 8 символов', lambda i: len(i) <= 8 ),
        form.regexp(REGEXP, '* Недопустимые символы в имени'),
        form.Validator('* Такое имя уже существует', lambda i: i not in htpasswd.users.keys())),
    form.Textbox('psw_new_user',
        form.Validator('* Длина пароля не должна превышать 8 символов', lambda i: len(i) <= 8 ),
        form.regexp(REGEXP, '* Недопустимые символы в пароле')),
    form.Textbox('info_new_user',
        form.Validator('* Длина инф. строки не должна превышать 30 символов', lambda i: len(i) <= 30)))

class Users:
    title = 'Пользователи'
    def GET(self):
        web.header('Content-Type', 'text/html; charset= utf-8')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')
        nuf = None
        ud = createUsers()
        if len(ud) <= MAX_USERS:
            nuf = newUserForm()
        return render.users(ud, nuf, self.title)

    def POST(self):
        valid = True
        newUser = None
        users = createUsers()
        if len(users) <= MAX_USERS:
            newUser = newUserForm()
        for k, f in users.iteritems():
            f.validates()
            if not f[k + '_del'].get_value():
                valid &= f.valid

        if newUser:
            newUser.validates()
            if newUser['new_user'].get_value():
                valid &= newUser.valid

        if not valid:
            return render.users(users, newUser, self.title)
        # сначала удаление
        tod = [n for n in users.keys() if users[n][n + '_del'].get_value()]
        save = tod != []
        if save:
            for n in tod:
                htpasswd.remove(n)
                del users[n]
        for k, f in users.iteritems():
            # запись изменений    
            psw = f[k + '_psw'].get_value()
            info = f[k + '_info'].get_value()
            if htpasswd.users[k] != (psw, '', info):
                htpasswd.users[k] = (psw, '', info)
                save = True
        if newUser:
            nu = newUser['new_user'].get_value()
            if nu:
                htpasswd.users[nu] = (newUser['psw_new_user'].get_value(), '', newUser['info_new_user'].get_value())
                save = True

        if save:
            htpasswd.save()

        return render.completion(self.title)
