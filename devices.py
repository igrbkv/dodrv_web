# -*- coding: utf-8 -*-
'''
Форма:
Сторожевой таймер.
    Драйвер [Нет, wafer5823wdt, indic_wdt]

Блинкера.
'''
from web import form
from config import render, DEBUG_PATH
from utils import restart_service, rewrite2 
from http import nocache
from configobj import ConfigObj
from subprocess import Popen, PIPE, call
import re

MODULES_PATH = DEBUG_PATH + '/etc/conf.d/modules'
WDT_DRIVERS = ['', 'wafer5823wdt', 'indic_wdt']

title = 'Устройства'

watchdogForm = form.Form(
    form.Dropdown('driver', [''] + WDT_DRIVERS, description = 'Драйвер'),)

blinkersForm = form.Form()

class Devices:
    def __init__(self):
        self.driver=''
        with open(MODULES_PATH) as mp:
            self.modules = map(str, mp.readlines())
        self.drvline=-1
        self.drivers=[]
        for line in self.modules:
            self.drvline +=1
            line = line.strip()
            if not line or line[0] == '#':
                continue
            line = line.split('=')
            if line[0] == 'modules':
                self.drivers += line[1].strip('"').split()
                for drv in self.drivers:
                    if drv in WDT_DRIVERS:
                        self.driver = drv
                        self.drivers.remove(drv)
                        break
                break

    def GET(self):
        nocache()

        wdtFrm = watchdogForm()
        wdtFrm['driver'].set_value(self.driver)

        blinkersFrm = blinkersForm()

        return render.devices(wdtFrm, blinkersFrm, title = title)


    def POST(self):
        wdtFrm = watchdogForm()
        wdtFrm.validates()
        blinkersFrm = blinkersForm()
        blinkersFrm.validates()
        
        # Запись изменений
        drv = wdtFrm['driver'].get_value()
        if drv != self.driver:

            if self.drvline != -1:
                # Удалить строку с драйверами
                self.modules.pop(self.drvline)

            if drv:
                self.drivers.append(drv)
            self.modules.append('modules="%s"\n' % (' '.join(self.drivers)))
            rewrite2(MODULES_PATH, self.modules)
            restart_service('watchdog')

        return render.completion(title)
