# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender

MAX_PULSE_DURATION_MS = 20

discreteForm = form.Form(
    form.Checkbox('inUse', description = 'Используется'),
    form.Textbox('alias', description = 'Имя'),
    form.Dropdown('phase', ['', 'A', 'B', 'C'], description = 'Фаза'),
    form.Textbox('circuitComponenet', description = 'Элемент цепи'),
    form.Dropdown('pulseDurationMs', [str(i) for i in xrange(MAX_PULSE_DURATION_MS + 1)], 'Мин. длительность импульса, мс'),
    form.Checkbox('discreteEmergency', description = 'файл аварии'),
    form.Checkbox('discreteSelfRecorder', description = 'самописец'),
    form.Checkbox('discreteOpc', description = 'OPC'))

class Discrete:
    title = ''


    def GET(self, dev, idx):
        web.header('Cache-Control', 'no-cache, must-revalidate')        
        self.title = 'Дискрет:' + channel + ':' + idx
        df = form.Form()
        d = xml['device'][dev]['discrete'][idx]
        df.inUse.set_value(d['in_use'] == "yes")
        df.alias.value = d['alias']
        df.phase.value = d['phase']
        df.circuitComponent = d['circuit_component']
        if d.has_key('trigger'):
            df.pulseDurationMs.value = d['trigger']['pulse_duration_ms']
            if d['trigger'].has_key('discrete_emergency'):
                df.discreteEmergency.set_value(True)
            if d['trigger'].has_key('discrete_self-recorder'):
                df.discreteSelfRecorder.set_value(True)
            if d['trigger'].has_key('discrete_opc'):
                df.discreteOpc.set_value(True)
        else:
            df.pulseDurationMs.value = '0'
            df.discreteEmergency.set_value(False)
            df.discreteSelfRecorder.set_value(False)
            df.discreteOpc.set_value(False)

        return render.discrete(df, title = self.title)

    def POST(self, dev, idx):
        df = discreteForm()
        df.validates()

        inUse = 'no'
        if df.inUse.get_value():
            inUse = 'yes'
        d = xml['device'][dev]['discrete'][idx]
        d['in_use'] = inUse
        d['alias'] = df.alias.value
        d['phase'] = df.phase.value
        d['circuit_component'] = df.circuitComponent.value
        pd = df.pulseDurationMs.value
        de = df.discreteEmergency.get_value()
        ds = df.discreteSelfRecorder.get_value()
        do = df.discreteOpc.get_value()
        if not d.has_key('trigger'):
            d[trigger] = {}
        d['trigger']['pulse_duration_ms'] = pd
        for 
        if de:
            d['trigger']['discrete_emergency'] = {}
        else:
            d[]
        if ds:
            d['trigger']['discrete_self-recorder'] = {}
        if do:
            d['trigger']['discrete_opc'] = {}

        
        return render.completion(self.title, 'Данные записаны')
