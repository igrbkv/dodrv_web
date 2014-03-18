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
Файл контрольной суммы[           ] [Выбрать]
[Выполнить]


Обновление ПО
Дистрибутив.
Файл дистрибутива 

etc/dodrv/version - файл с версией dodrv следующего формата:
1.0.0
2012

Выводится во вкладке "О программе"

/etc/dodrv/saveconfigs - список файлов конфигурации сохраняемых при обновлении.
Папка для сохранения - /etc/dodrv/<N>/etc/..., где N - первое число версии
'''

import web
from web import form
from config import xml, render, EMERGENCY_PATH, RECORDER_PATH, DEBUG_PATH, FILTERS
from http import nocache
from subprocess import Popen, PIPE, call
from syslog import syslog
import time
import os
import shutil
import ctypes
from signal import SIGUSR1
from calendar import timegm

title = 'Сервис'

MD5SUMS_UPLOAD_PATH = DEBUG_PATH + '/md5sums'

NOTE_NO_FILE = 'Файл не задан'
NOTE_ERROR_UPLOAD = 'Ошибка приема файла'
LOG_REBOOT = 'Перезапуск по команде администратора'

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

class UploadFile(form.Input):
    def get_type(self):
        return 'file'

upgradeForm = form.Form(
    UploadFile('dist', description = 'Файл дистрибутива'),
    #UploadFile('md5sums', description = 'Файл с контрольной суммой'),
    form.Checkbox('save_config', value = 'value', description = 'Сохранить конфигурацию'),
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


def remove_path(path, delta):
    '''
    return <число удаленных файлов>
    '''
    n = 0
    ct = timegm(time.gmtime())
    for f in [f for f in os.listdir(path) if not f in [".",".."]]:
        fp = path + '/' + f
        fi = os.stat(fp)
        dt = ct - fi.st_mtime
        if (ct - fi.st_mtime) > delta:
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
    sec = int(xml["emergency"]["max_file_length_s"])
    n = remove_path(EMERGENCY_PATH, sec)
    sec = int(xml["self-recorder"]["max_file_length_hour"])*60*60
    n += remove_path(RECORDER_PATH, sec)
    return n

def upgrade(save_config):
    if save_config:
        call(['sysupgrade.sh', '1'])
    else:
        call(['sysupgrade.sh'])


class Service:
    i = None

    def GET(self):
        nocache()

        return render.service(rebootForm(), startForm(), 
            removeForm(), upgradeForm(), title = title)


    def POST(self):
        # self.i = web.input(dist={}, md5sums={})
        self.i = web.input(dist={})
        if self.i.form_action == 'reboot':
            reboot()
        elif self.i.form_action == 'start':
            start()
        elif self.i.form_action == 'remove':
            remove()
        else:
            upgradeFrm = upgradeForm()
            upgradeFrm.validates()
            if ('dist' in self.i) and upgradeFrm['dist'].get_value() and\
                    upgradeFrm['dist'].get_value().strip():
                filepath = self.i.dist.filename.replace('\\','/')
                filename = '%s/%s' % (DEBUG_PATH, filepath.split('/')[-1])
                distr = open(filename,'w')
                shutil.copyfileobj(self.i.dist.file, distr)
                distr.close()
                #if ('md5sums' in self.i) and upgradeFrm['md5sums'].get_value()\
                #        and upgradeFrm['md5sums'].get_value().strip():
                #    sums = open(MD5SUMS_UPLOAD_PATH,'w')
                #    shutil.copyfileobj(self.i.md5sums.file, sums)
                #    sums.close()
                upgrade(upgradeFrm['save_config'].get_value())
            else:
                upgradeFrm['dist'].note = NOTE_NO_FILE
                return render.service(rebootForm(), startForm(), 
                    removeForm(), upgradeFrm, title = title)

        return render.completion(title, text='Команда выполнена')
