# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, rewriteConfigXml
from utils import restartFilters

MAX_PULSE_DURATION_MS = 20

discreteForm = form.Form(
    form.Checkbox('in_use', value = 'value', description = 'Используется'),
    form.Textbox('alias', description = 'Имя'),
    form.Dropdown('phase', ['', 'A', 'B', 'C'], description = 'Фаза'),
    form.Textbox('circuit_component', description = 'Элемент цепи'),
    form.Checkbox('inverted', value = 'value', description = 'Инвертировать'))

filterForm = form.Form(
    form.Dropdown('pulse_duration_ms', [str(i) for i in xrange(MAX_PULSE_DURATION_MS + 1)], description = 'Мин. длительность импульса, мс'),
    form.Checkbox('discrete_emergency', value = 'value', description = 'Запись в файл аварии'),
    form.Checkbox('discrete_self-recorder', value = 'value', description = 'Запись в самописец'),
    form.Checkbox('discrete_opc', value = 'value', description = 'Запись в OPC'))

class Discrete:
    title = ''

    def GET(self, dev, idx):
        web.header('Content-Type', 'text/html; charset= utf-8')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')
        self.title = u'Дискрет:' + dev + ':' + idx
        df = discreteForm()
        ff = filterForm()
        df.dev = dev
        df.id = idx
        d = xml['device'][dev]['discrete'][idx]
        df.in_use.set_value(d['in_use'] == "yes")
        for k in ('alias', 'phase', 'circuit_component'):
            df[k].value = d[k]
        df.inverted.set_value(d['inverted'] == "yes")
        flt = 'trigger'
        if flt in d.keys():
            par = 'pulse_duration_ms'
            ff[par].value = d[flt][par]
            for par in ('discrete_emergency', 'discrete_self-recorder', 'discrete_opc'):
                if par in d[flt].keys():
                    ff[par].set_value(True)

        return render.discrete(df, ff, title = self.title)

    def POST(self, dev, idx):
        df = discreteForm()
        ff = filterForm()
        df.validates()
        ff.validates()

        d = xml['device'][dev]['discrete'][idx]
        
        inUse = 'no'
        if df.in_use.get_value():
            inUse = 'yes'
        d['in_use'] = inUse
        for k in ('alias', 'phase', 'circuit_component'):
            d[k] = df[k].value 
        inverted = 'no'
        if df.inverted.get_value():
            inverted = 'yes'
        d['inverted'] = inverted

        par = 'trigger'
        if par not in d.keys():
            d[par] = {}
        d[par]['pulse_duration_ms'] = ff.pulse_duration_ms.value
        for k in ('discrete_emergency', 'discrete_self-recorder', 'discrete_opc'):
            if ff[k].get_value():
                d[par][k] = {}
            elif k in d[par].keys():
                d[par].pop(k)

        xml['device'][dev]['discrete'][idx] = d
        
        rewriteConfigXml()
        restartFilters(dev)
        
        return render.completion(self.title)
