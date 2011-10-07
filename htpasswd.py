# -*- coding: utf-8 -*-
'''
1. Структура файла паролей:
    <имя>:[<пароль>]:[<доп_инфо>]
    ...
2. Администратор - admin, остальные - пользователи
с любыми именами
3. При отсутствии файла паролей вход только под
логином admin и паролем admin.
'''

from config import PASSWD_FILE_PATH

class Htpasswd:
    users = {}
    def __init__(self, path):
        self.path = path
        self._load()

    def _load(self):
        self.users['admin'] = ('admin', '')
        try:
            with open(self.path, 'r') as f:
                lst = f.readlines()
            for l in lst:
                l = l.strip().split(':')
                print l
                self.users[l[0]] = (l[1], l[2])
        except IOError:
            pass

    def remove(self, name):
        if name in self.users.keys():
            del self.users[name]

    def save(self):
        print self.users
        lst = ['%s:%s:%s\n' % (k.encode('utf-8'), v[0].encode('utf-8'), v[1].encode('utf-8')) 
            for k, v in self.users.iteritems()]
        print lst
        with open(self.path, 'w+') as f:
            f.writelines(lst)
    def userValid(self, login, psw):
        return login in self.users.keys() and self.users[login][0] == psw

htpasswd = Htpasswd(PASSWD_FILE_PATH)


