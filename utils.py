# -*- coding: utf-8 -*-

import types
from shutil import copy, move
from subprocess import Popen
from os import waitpid, close
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
 
