# -*- coding: utf-8 -*-

import web
from config import render
from subprocess import Popen, PIPE
from datetime import datetime

class System:
    title = 'Система'
    def GET(self):
        '''
        state=(mem_used_percnt, mem_used, cpu, datetime)
        '''
        web.header('Content-Type', 'text/html; charset= utf-8')
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
        print state
        return render.system(state, self.title)
