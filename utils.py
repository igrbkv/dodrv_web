# -*- coding: utf-8 -*-

import types
from shutil import copy, move
from subprocess import Popen
from os import waitpid
import syslog

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
        suf = 'фильтра pov%s' % which
        which = '.pov' + which
    else:
        suf = 'фильтров'

    try:
        p = Popen('/etc/init.d/dofilters%s restart' % which, shell=False)
        waitpid(p.pid, 0)
        syslog.syslog('Перезапуск ' + suf)
    except:
        syslog.syslog(syslog.LOG_ERR, 'Ошибка перезапуска ' + suf)

