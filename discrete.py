# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender

MAX_PULSE_DURATION_MS = 20

discreteForm = form.Form(
    form.Checkbox('inUse', value = 'value', checked = True, description = 'Используется'),
    form.Textbox('alias', description = 'Имя'),
    form.Dropdown('phase', ['', 'A', 'B', 'C'], description = 'Фаза'),
    form.Textbox('circuitComponent', description = 'Элемент цепи'),
    form.Checkbox('inverted', value = 'value', checked = True, description = 'Инвертировать'))

filterForm = form.Form(
    form.Dropdown('pulseDurationMs', [str(i) for i in xrange(MAX_PULSE_DURATION_MS + 1)], description = 'Мин. длительность импульса, мс'),
    form.Checkbox('discreteEmergency', value = 'value', checked = True, description = 'Запись в файл аварии'),
    form.Checkbox('discreteSelfRecorder', value = 'value', checked = True, description = 'Запись в самописец'),
    form.Checkbox('discreteOpc', value = 'value', checked = True, description = 'Запись в OPC'))

class Discrete:
    title = ''

    def GET(self, dev, idx):
        web.header('Cache-Control', 'no-cache, must-revalidate')        
        self.title = u'Дискрет:' + dev + ':' + idx
        df = discreteForm()
        ff = filterForm()
        df.dev = dev
        df.id = idx
        d = xml['device'][dev]['discrete'][idx]
        df.inUse.set_value(d['in_use'] == "yes")
        df.alias.value = d['alias']
        df.phase.value = d['phase']
        df.circuitComponent.value = d['circuit_component']
        df.inverted.set_value(d['inverted'] == "yes")
        if 'trigger' in d.keys():
            ff.pulseDurationMs.value = d['trigger']['pulse_duration_ms']
            if 'discrete_emergency' in d['trigger'].keys():
                ff.discreteEmergency.set_value(True)
            if 'discrete_self-recorder' in d['trigger'].keys():
                ff.discreteSelfRecorder.set_value(True)
            if 'discrete_opc' in d['trigger'].keys():
                ff.discreteOpc.set_value(True)
        else:
            ff.pulseDurationMs.value = '0'
            ff.discreteEmergency.set_value(False)
            ff.discreteSelfRecorder.set_value(False)
            ff.discreteOpc.set_value(False)

        return render.discrete(df, ff, title = self.title)

    def POST(self, dev, idx):
        df = discreteForm()
        ff = filterForm()
        df.validates()
        ff.validates()

        d = xml['device'][dev]['discrete'][idx]
        
        inUse = 'no'
        if df.inUse.get_value():
            inUse = 'yes'
        d['in_use'] = inUse
        d['alias'] = df.alias.value
        d['phase'] = df.phase.value
        d['circuit_component'] = df.circuitComponent.value
        inverted = 'no'
        if df.inverted.get_value():
            inverted = 'yes'
        d['inverted'] = inverted
        pd = ff.pulseDurationMs.value
        de = ff.discreteEmergency.get_value()
        ds = ff.discreteSelfRecorder.get_value()
        do = ff.discreteOpc.get_value()
        if 'trigger' not in d.keys():
            d['trigger'] = {}
        d['trigger']['pulse_duration_ms'] = pd
        for nv, ov in zip((de, ds, do), ('discrete_emergency', 'discrete_self-recorder', 'discrete_opc')):
            if nv:
                d['trigger'][ov] = {}
            elif ov in d['trigger'].keys():
                d['trigger'].pop(ov)

        xml['device'][dev]['discrete'][idx] = d
        return render.completion(self.title)
