# -*- coding: utf-8 -*-
"""
Отображение состояния синхронизации по GPS или NTP.
1. Текущее состояние синхронизации определяется двумя командами:
    ntpq -p
    ntptime
    Состояние:
    1) Сервис ntpd не запущен
        >ntpq -p  
        >ntpq: read: Connection refused
    2) Часы синхронизированы
        ntpq -p в колонке remote адрес сервера начинается с '+' или '*' или 'o'
        в колонке reach 377
        ntptime returns code 0 (OK)
        offset - смещение относительно эталоного времени (мкс)
    3) Синхронизируются
        a) ntpq -p в колонке remote адрес сервера начинается с ' '
        в колонке reach не 0, а в t не '-'
        b) с '+' или '*' или 'o'(PPS) 
        ntptime returns code 5 (ERROR)
        в status'е UNSYNC
    4) Нет связи с сервером
        A)
        >ntpq -p
        >Temporary failure in name resolution
        b) ntpq -p
        в колонке reach 0 в колонке t '-'


2. Формат страницы:
Синхронизация

0. Синхронизация не используется.
1'. Сервис ntpd не запущен.
1". Нет связи с сервером времени. Синхронизация невозможна.
2. Часы синхронизированы.
Расхождение с эталонным временем: NNNN мкс
3. Связь установлена. Производится корректировка часов.
"""
import web
from config import render
from utils import sync_mode
from subprocess import Popen, PIPE
from dotime import curPort, serverAddress

title = 'Синхронизация'

def ntpqp():
    '''
    >ntpq -p
    >remote           refid      st t when poll reach   delay   offset  jitter
    >=========================================================================
    >*ntp1.vniiftri.r .PPS.       1 u    6   16  377   11.941    0.040   0.371
    
    return <err_msg>, {} или '', {remote:<adr_serv>, ...}
    '''
    err = ''
    res = {}
    par = ['ntpq', '-p']
    rcs = Popen(par, stdout = PIPE).communicate()[0].split('\n')
    if len(rcs) < 3:
        err = rcs[0]
    else:
        res = dict(zip(rcs[0].split(), rcs[2].split()))
    return err, res

def ntptime():
    '''
    Берет из вывода команды ntptime
    код возврата ntp_gettime() и смещение ntp_adjtime()
    return code, offset
    '''
    par = ['ntptime']
    rcs = Popen(par, stdout = PIPE).communicate()[0].split('\n')
    return rcs[0].split()[3], rcs[5].split()[1]


class SyncState:
    def GET(self):
        """
        """
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')
        
        text = []
        smode = sync_mode()
        if smode == 'manually':
            text.append(u'Синхронизация не используется.')
        else:
            if smode == 'gps':
                server = 'GPS (COM%d)' % curPort()
            else:
                server = serverAddress()
            err, pval = ntpqp()
            if err or (pval['t'] == '-' and pval['reach'] == '0'):
                text.append('Нет связи с ' + server +
                    '. Синхронизация невозможна.')
                #if err:
                #    text.append('Ошибка: ' + err)
            else:
                if pval['remote'][0] in ['+', '*', 'o']:
                    code, offset = ntptime()
                    if pval['reach'] == '377' and code == '0':
                        text.append('Часы синхронизированы c ' + server + '.')
                        text.append('Расхождение с эталонным временем: ' +
                            offset + ' мкс')
                    
                if not text:
                    text.append('Связь установлена c ' + server + 
                        '. Производится корректировка часов.')
        return render.syncstate(text, title = title)
