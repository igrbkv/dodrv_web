# -*- coding: utf-8 -*-

import web
from config import render, xml, POV_STAT, MAX_POV, DEBUG_PATH
from subprocess import Popen, PIPE
from datetime import datetime


def _povsStatistic():
    try:
        d = {}
        cur = ''
        with open(POV_STAT, 'r') as f:
            lst = filter(lambda l: l, map(str.strip, f.readlines()))
        for l in lst:
            l = [s.strip() for s in l.split(':')]
            if l[0] == 'pov':
                cur = l[1]
                d[cur] = {}
            else:
                d[cur][l[0]] = l[1]
        return d
    except IOError:
        pass

class PovStatistic:
    '''
    Статистика канала
    '''
    def GET(self, dev):
        self.title = 'Статистика канала ' + dev.encode('utf-8')
        ps = _povsStatistic()
        return render.pov(ps[dev], self.title)
 
class System:
    title = 'Система'

  
    def _sysState(self):
        # первое значение cpu idle - усреднение с момента загрузки
        # поэтому delay 1c и 2й вывод
        vmstat = Popen(['vmstat', '1', '2'], stdout=PIPE)
        # занято на диске
        try:
            df = Popen(['df', '-h', '/dev/sda4'], stdout=PIPE).communicate()[0].split('\n')[1].split()
            state = (df[2], df[4])
        except:
            state = ('', '')
        # используется памяти
        mem = Popen(['free'], stdout=PIPE).communicate()[0].split()
        state += (mem[8], str(int(mem[8])*100/int(mem[7])))
        # cpu idle: 15 поле в 4 строке вывода
        state += (str(100-int(vmstat.communicate()[0].split('\n')[3].split()[14])),)
        state += (datetime.now().strftime('%H:%M:%S %d/%m/%y'),)
        return state

    def _povState(self, first, second):
        '''
        first, second - статистики разнесенные по времени
        return [(pov_num, state), ...]        '''
        ps = []
        for i in map(str, xrange(MAX_POV)):
            if i in first.keys():
                if xml['device'][i]['in_use'] == "yes":
                    if first[i]['bytes_read'] != second[i]['bytes_read']:
                        state = 1
                    else: 
                        state = -1
                else:
                    state = 0
                ps.append((i, state))
        return ps

    def GET(self):
        '''
        sysState=(mem_used_percnt, mem_used, cpu, datetime)
        povState=[(pov_num, state)], где state:
        1 - OK
        0 - канал не используется
        -1 - данные не поступают с ПУ

        '''
        web.header('Content-Type', 'text/html; charset= utf-8')
        first = _povsStatistic()
        sysState = self._sysState()
        povState = self._povState(first, _povsStatistic())
        return render.system(sysState, povState, self.title)
 
VERSION_PATH = DEBUG_PATH + '/etc/dodrv/version'

class Version:
    '''
    Вывод файла файла /etc/dodrv/version:
    <номер_версии>, напр. 1.0.0
    <год_выпуска>, напр. 2012
    '''
    title = 'Интерфейс регистратора ПАРМА РП4.06М'

    def GET(self):
        ver = []
        with open(VERSION_PATH, 'r') as f:
            ver = map(str.strip, f.readlines())

        return render.version(ver, self.title)
