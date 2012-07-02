# -*- coding: utf-8 -*-

import types
from shutil import copy, move
from subprocess import Popen, check_call, CalledProcessError, PIPE
from os import waitpid, close, tmpnam, rename
import syslog
import mmap 
import posix_ipc 
from decimal import getcontext, Decimal

def getAllFunctions(module):
    functions = {}
    for f in [module.__dict__.get(a) for a in dir(module)
        if isinstance(module.__dict__.get(a), types.FunctionType)]:
        functions[f.__name__] = f
    return functions

def rewrite(filePath, str):
    try:
        tmp = open(filePath + '.tmp', 'w+')
        tmp.write(str)
        tmp.flush()
        tmp.close()

        copy(filePath, filePath + '~')
        move(filePath + '.tmp', filePath)
    finally:
        return False

    return True

def restart_service(name):
    '''
    Перезапуск сервиса <name>
    '''
    path = '/etc/init.d' + name
    try:
        check_call(['path', 'restart'])
        syslog.syslog('Сервис ' + name + ' перезапущен')
    except:
        syslog.syslog('Ошибка перезапуска сервиса ' + name)

def add_service(name, level = 'default'):
    '''
    Добавление сервиса в runlevel level и запуск
    '''
    try:
        check_call(['rc-update', 'add', name, level])
        syslog.syslog('Сервис ' + name + ' запущен')
    except:
        syslog.syslog('Ошибка запуска сервиса ' + name)

def del_service(name, level = 'default'):
    '''
    Удаление сервиса из runlevel level и останов
    '''
    try:
        check_call(['rc-update', 'del', name, level])
        syslog.syslog('Сервис ' + name + ' остановлен')
    except CalledProcessError:
        # Игнорировать ошибку для уже остановленного сервиса
        pass
    except:
        syslog.syslog('Ошибка останова сервиса ' + name)


def restartFilters(which=''):
    if which:
        suf = 'фильтра pov' + which.encode('utf-8')
        which = '.pov' + which
    else:
        suf = 'фильтров'

    try:
        p = Popen('/etc/init.d/dofilters%s restart' % which, shell=False)
        waitpid(p.pid, 0)
        syslog.syslog('Перезапуск ' + suf)
    except:
        syslog.syslog('Ошибка перезапуска ' + suf)

def readShmem(dev):
    '''
    Считать данные из разделяемой памяти устройства dev как массив строк
    вида:
    <name>,N,<value1>...
    и привести к виду:
    [[<name>,N,<value1>,...], ...]
    '''
    lines = []
    name = str("/pov" + dev)
    try:
        mem = posix_ipc.SharedMemory(name)
        sem = posix_ipc.Semaphore(name)
        fmap = mmap.mmap(mem.fd, mem.size)
        close(mem.fd)
        # антиблокиратор на всякий случай 
        sem.acquire(1.0)
        l = fmap.readline().strip()
        while l:
            lines.append(l.split(','))
            l = fmap.readline().strip()
        sem.release()
        fmap.close()
        sem.close()

    except:
        es = u'Ошибка чтения разделяемой памяти ' + name
        syslog.syslog(es.encode('utf-8'))

    return lines


prefixes = [('', ''), ('k', 'к'), ('M', 'М'), ('G', 'Г'), ('T', 'Т'), ('P', 'П'), ('E', 'З'), ('f', 'ф'), ('n', 'н'), ('u', 'мк'), ('m', 'м')]

def toSI(v, prec=4, ru=0):
    '''
    Преобразовние числа в формат Си
    @param v строка! с числом
    @param prec значащих цифр в числе
    @param ru 1 - русский суфикс

    '''
    getcontext().prec=prec
    d = Decimal(v)
    td = d.as_tuple()
    if td.digits == (0,):
        return '0'
    i = (len(td.digits) + td.exponent - 1)/3
    d = (d/Decimal(str(1000 ** i))).to_eng_string()
    p = prefixes[i][ru]
    return '%s%s' % (d, p)


ticks = u'▁▂▃▅▆▇'

def spark_string(ints):
    """Returns a spark string from given iterable of ints."""
    step = ((max(ints)) / float(len(ticks) - 1)) or 1
    ss = u''.join(ticks[int(round(i / step))] for i in ints)
    return ss.encode('utf-8')

def rewrite(fpath, lines):
    '''
    Перезаписывает файл fpath содержимым lines 
    '''
    tpath = tmpnam()
    with open(tpath, 'w') as mc:
        mc.writelines(lines)
    rename(tpath, fpath)

def sync_mode():
    '''
    Текущий режим синхронизации
    return  'manually', 'ntp' или 'gps'
    '''
    ntpd = False
    ntp_pps = False
    par = ['rc-status']
    rcs = Popen(par, stdout = PIPE).communicate()[0].split('\n')
    for rc in rcs:
        if not ntpd and 'ntpd' in rc and 'started' in rc:
            ntpd = True
        if not ntp_pps and 'ntp-pps' in rc and 'started' in rc:
            ntp_pps = True
    if ntpd:
        if ntp_pps:
            return 'gps'
        return 'ntp'
    return 'manually'
 
