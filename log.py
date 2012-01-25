# -*- coding: utf-8 -*-
'''
Вывод журнала регистратора.
Для журнала берется содержимое всех файлов из папки LOG_PATH, отсортированных
по времени изменения.
Мetalog для этого должен быть настроен на ограничение числа файлов в
папке и их размера.
'''
import web
from config import render, xml, LOG_PATH
from http import nocache
from stat import S_ISREG, ST_MTIME, ST_MODE
from os import stat, listdir, path

title = "Журнал"

class Log:
    def GET(self):
        nocache()
        data = ''
        entries = [path.join(LOG_PATH, fn) for fn in listdir(LOG_PATH)]
        entries = [(stat(fn), fn) for fn in entries]
        entries = [(s[ST_MTIME], p) for s, p in entries if S_ISREG(s[ST_MODE])]
        for entry in sorted(entries):
            with open(entry[1]) as f:
                data += f.read()

        return render.log(data, title=title)

