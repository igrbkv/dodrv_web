# -*- coding: utf-8 -*-

import types
from shutil import copy, move
from subprocess import Popen, check_call, CalledProcessError, PIPE
from os import waitpid, close, tmpnam, rename, read, lseek, write
import struct
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

        try:
            copy(filePath, filePath + '~')
        except:
            pass
        move(filePath + '.tmp', filePath)
    finally:
        return False

    return True


def restart_service(name):
    '''
    Перезапуск сервиса <name>
    '''
    path = '/etc/init.d/' + name
    try:
        check_call([path, 'restart'])
        syslog.syslog('Сервис ' + name + ' перезапущен')
    except:
        syslog.syslog('Ошибка перезапуска сервиса %s' % name)

def add_service(name, level = 'default', start = True):
    '''
    Добавление сервиса в runlevel level и запуск
    '''
    state = 0
    try:
        check_call(['rc-update', 'add', name, level])
        syslog.syslog('Сервис ' + name + ' установлен')
        if start:
            state = 1
            check_call(['/etc/init.d/' + name, 'start'])
            syslog.syslog('Сервис ' + name + ' запущен')
    except:
        syslog.syslog('Ошибка %s сервиса %s' % 
                ('установки' if state == 0 else 'запуска', name))

def del_service(name, level = 'default', stop = True):
    '''
    Удаление сервиса из runlevel level и останов
    '''
    state = 0
    try:
        if stop:
            check_call(['/etc/init.d/' + name, 'stop'])
            syslog.syslog('Сервис ' + name + ' остановлен')
        state = 1
        check_call(['rc-update', 'del', name, level])
        syslog.syslog('Сервис ' + name + ' удален')
    except CalledProcessError:
        # Игнорировать ошибку для уже остановленного сервиса
        pass
    except:
        syslog.syslog('Ошибка %s сервиса %s' % 
                ('останова' if state == 0 else 'удаления', name))


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

def recorderMode(value=None):
    '''
    @param value если задан, записывается в /dev/shm/recorder_mode
    @return предыдущее значение /dev/shm/recorder_mode
    '''
    fmt = '=i'
    try:
        mem = posix_ipc.SharedMemory('/recorder_mode')
        sem = posix_ipc.Semaphore('/wdog')
        # антиблокиратор на всякий случай 
        sem.acquire(1.0)
        buf = read(mem.fd, struct.calcsize(fmt))
        mode = struct.unpack(fmt, buf)
        if value != None:
            lseek(mem.fd, 0, 0)
            write(mem.fd, struct.pack(fmt, value))
        sem.release()
        close(mem.fd)
        sem.close()
        return mode[0]
    except:
        pass
    return -1


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

def rewrite2(fpath, lines):
    '''
    Перезаписывает файл fpath содержимым lines 
    '''
    with open(fpath, 'w') as mc:
        mc.writelines(lines)

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



