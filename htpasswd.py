# -*- coding: utf-8 -*-
'''
1. Структура файла паролей:
    <имя>:[<пароль>]:[<опции>]:[<доп_инфо>]
    ...
2. Администратор - admin, остальные - пользователи
с любыми именами
3. При отсутствии файла паролей вход только под
логином admin и паролем admin.
4. Поле <оцпии> зарезервировано, например для флагов интерфейса - чистый html 
или javascript и т.п.
5. Пароль в файле не кодируется, т.к. все равно передается через незащищенное 
соединение
'''

from config import PASSWD_FILE_PATH

class Htpasswd:
    users = {}
    def __init__(self, path):
        self.path = path
        self._load()

    def _load(self):
        self.users['admin'] = ('admin', '', '')
        try:
            with open(self.path, 'r') as f:
                lst = f.readlines()
            for l in lst:
                l = l.strip().split(':')
                info = ''
                for w in l[3:]:
                    info += w
                self.users[l[0]] = (l[1], l[2], info)
        except IOError:
            pass

    def remove(self, name):
        if name in self.users.keys():
            del self.users[name]

    def save(self):
        lst = ['%s:%s:%s:%s\n' % (k.encode('utf-8'), v[0].encode('utf-8'), v[1].encode('utf-8'), v[2].encode('utf-8'))
            for k, v in self.users.iteritems()]
        with open(self.path, 'w+') as f:
            f.writelines(lst)

    def userValid(self, login, psw):
        return login in self.users.keys() and self.users[login][0] == psw

htpasswd = Htpasswd(PASSWD_FILE_PATH)


