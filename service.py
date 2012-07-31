# -*- coding: utf-8 -*-
'''
http://webpy.org/cookbook/limiting_upload_size
http://webpy.org/cookbook/storeupload/
http://webpy.org/cookbook/fileupload

Форма:
Сервис

1. Перезапуск
[Выполнить]

2. Запись файлов
[Выполнить]

3. Удаление файлов аварий и самописцев
[Выполнить]

4. Обновление ПО
[x] Сохранить файлы конфигурации
Файл дистрибутива[           ] [Выбрать]
[Выполнить]


Обновление ПО
Дистрибутив.
Файл дистрибутива 

etc/dodrv/version - файл с версией dodrv следующего формата:
    Интерфейс регистратора ПАРМА РП4.06М
    Версия 1.0.0
    Год 2012
    www.parma.spb.ru 
    parma@parma.spb.ru

Выводится во вкладке "О программе"

/etc/dodrv/saveconfigs - список файлов конфигурации сохраняемых при обновлении.
Папка для сохранения - /etc/dodrv/<N>/etc/..., где N - первое число версии
'''

import web
from web import form
from config import render, EMERGENCY_PATH, RECORDER_PATH, DEBUG_PATH, FILTERS
from http import nocache
from subprocess import Popen, PIPE, call
from syslog import syslog
import time
import os
import shutil
import ctypes
from signal import SIGUSR1

title = 'Сервис'

UPLOAD_PATH = DEBUG_PATH + '/dodrv.gz'
NOTE_NO_FILE = u'Файл не задан'
LOG_REBOOT = 'Перезапуск по команде администратора'
MAX_TIME_DELTA = 60*60  # 1 час

rebootForm = form.Form(
    form.Button('form_action', value = 'reboot', type = 'submit', 
        html = u'Выполнить'))

# FIXME Добавить длительность записи
startForm = form.Form(
    form.Button('form_action', value = 'start', type = 'submit', 
        html = u'Выполнить'))

removeForm = form.Form(    
    form.Button('form_action', value = 'remove', type = 'submit', 
        html = u'Выполнить'))

upgradeForm = form.Form(
    form.Button('form_action', value = 'upgrade', type = 'submit', 
        html = u'Выполнить'))

def reboot():
    '''
    Перезагрузка регистратора
    '''
    syslog(LOG_REBOOT)
    call(['reboot'])

class sigval_t(ctypes.Union):
    _fields_ = [
        ('sigval_int', ctypes.c_int),
        ('sigval_ptr', ctypes.c_void_p)
    ]


def start(sec=0):
    '''
    Пуск регистратора 
    sec - длительность файла
    '''
    libc = ctypes.CDLL(None)
    sigqueue = libc.sigqueue
    sigqueue.argtypes = [ctypes.c_int, ctypes.c_int, sigval_t]
    sigqueue.restype = ctypes.c_int

    duration = sigval_t(sec)

    par = ['pidof', FILTERS]
    pids = Popen(par, stdout = PIPE).communicate()[0].split()
    for pid in pids:
        sigqueue(int(pid), SIGUSR1, duration)


def remove_path(ct, path):
    '''
    return <число удаленных файлов>
    '''
    n = 0
    for f in [f for f in os.listdir(path) if not f in [".",".."]]:
        fp = path + '/' + f
        fi = os.stat(fp)
        ft = time.localtime(fi.st_mtime)
        dt = ct - ft
        if dt.seconds > MAX_TIME_DELTA:
            try:
                os.remove(fp)
                syslog('Удален файл:' + fp)
                n += 1
            except:
                pass
    return n

def remove():
    '''
    Удаление файлов аварий и самописцев.
    Удаляются файлы, созданные не позднее MAX_TIME_DELTA секунд назад.

    '''
    syslog('Очистка диска')
    ct = time.localtime()
    n = remove_path(ct, EMERGENCY_PATH)
    n += remove_path(ct, RECORDER_PATH)
    return n

def upgrade():
    pass

class Service:
    i = None

    def GET(self):
        nocache()

        return render.service(rebootForm(), startForm(), 
            removeForm(), upgradeForm(), title = title)

    def upload(self):
        # Из windows-пути взять имя файла
        # filepath = self.i.myfile.fname.replace('\\','/')
        # filename = filepath.split('/')[-1]
        try:
            target = file(UPLOAD_PATH, "wb")
            shutil.copyfileobj(self.i.myfile.file, target)
            target.close()
        except:
            return False
        return True


    def POST(self):
        self.i = web.input(myfile={})
        if self.i.form_action == 'reboot':
            reboot()
        elif self.i.form_action == 'start':
            start()
        elif self.i.form_action == 'remove':
            remove()
        else:
            if 'myfile' in self.i:
                if self.i.myfile.filename:
                    if self.upload():
                        upgrade() 
                    else:
                        raise web.seeother('config/service')

                else:
                    upgradeFrm = upgradeForm()
                    upgradeFrm.note = NOTE_NO_FILE
                    return render.service(rebootForm(), startForm(), 
            removeForm(), upgradeFrm, title = title)

        return render.completion(title, text='Команда выполнена')
