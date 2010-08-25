# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender

MIN_INTEGRATION_INTERVAL_MS = 10
MAX_INTEGRATION_INTERVAL_MS = 100
MIN_HARMONIC_NUM = 1
MAX_HARMONIC_NUM = 20
MIN_EMERGENCY_DURATION = 0

FLOAT_REGEXP = '[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'
DC_COMPONENT_NOTE = 'Должно быть число'
COEF1_NOTE = 'Должно быть число не меньшее 1.' 
RMS_NOTE = 'Должно быть число не меньшее 0.' 

analogForm = form.Form(
    form.Checkbox('inUse', value = 'value', checked = True, description = 'Используется'),
    form.Textbox('alias', description = 'Имя'),
    form.Dropdown('phase', ['', 'A', 'B', 'C'], description = 'Фаза'),
    form.Textbox('circuitComponent', description = 'Элемент цепи'),
    form.Dropdown('ADC', [adc for adc in xml['ADCs'].keys()], description = 'ADC'),
    form.Dropdown('sinusoid', [('yes', '~'), ('no','-')], description = 'Ток'),
    form.Textbox('dcComponent', 
        form.Validator(DC_COMPONENT_NOTE, bool),
        form.regexp(FLOAT_REGEXP, DC_COMPONENT_NOTE),
        description = 'Пост. составляющая, В или А'),
    form.Textbox('coef1', 
        form.Validator(COEF1_NOTE, bool),
        form.regexp(FLOAT_REGEXP, COEF1_NOTE),
        form.Validator(COEF1_NOTE, lambda i: float(i) >= 1.0),
        description = 'Коэффициент преобраз. из первичных цепей'))

rmsForm = form.Form(
    form.Dropdown('rmsIntegrationIntervalMs', [str(i) for i in xrange(MIN_INTEGRATION_INTERVAL_MS, MAX_INTEGRATION_INTERVAL_MS, 10)], description = 'Интервал интегрирования, мс'),
    form.Checkbox('rmsAnalogEmergency', value = 'value', description = 'Запись в файл аварии'),
    form.Textbox('rmsTopThreshold', 
        form.regexp(FLOAT_REGEXP, RMS_NOTE),
        description = 'Верхняя граница'),
    form.Textbox('rmsBottomThreshold', 
        form.regexp(FLOAT_REGEXP, RMS_NOTE),
        description = 'Нижняя граница'),
    form.Dropdown('rmsMaxDuration', [str(i) for i in range(MIN_EMERGENCY_DURATION, 10) + range(10,110,10)], description = 'Минимальная длительность аварии, мс'),
    form.Checkbox('rmsAnalogSelfRecorder', value = 'value', description = 'Запись в самописец'),
    form.Checkbox('rmsAnalogOpc', value = 'value', description = 'Запись в OPC'))

zeroForm = form.Form(
    form.Dropdown('zeroIntegrationIntervalMs', [str(i) for i in xrange(MIN_INTEGRATION_INTERVAL_MS, MAX_INTEGRATION_INTERVAL_MS, 10)], description = 'Интервал интегрирования, мс'),
    form.Dropdown('zeroIdB', [], description = 'Фаза B'),
    form.Dropdown('zeroIdC', [], description = 'Фаза C'),
    form.Checkbox('zeroAnalogEmergency', value = 'value', description = 'Запись в файл аварии'),
    form.Checkbox('zeroAnalogSelfRecorder', value = 'value', description = 'Запись в самописец'),
    form.Checkbox('zeroAnalogOpc', value = 'value', description = 'Запись в OPC'))

positiveForm = form.Form(
    form.Dropdown('positiveIntegrationIntervalMs', [str(i) for i in xrange(MIN_INTEGRATION_INTERVAL_MS, MAX_INTEGRATION_INTERVAL_MS, 10)], description = 'Интервал интегрирования, мс'),
    form.Dropdown('positiveIdB', [], description = 'Фаза B'),
    form.Dropdown('positiveIdC', [], description = 'Фаза C'),
    form.Checkbox('positiveAnalogEmergency', value = 'value', description = 'Запись в файл аварии'),
    form.Checkbox('positiveAnalogSelfRecorder', value = 'value', description = 'Запись в самописец'),
    form.Checkbox('positiveAnalogOpc', value = 'value', description = 'Запись в OPC'))

negativeForm = form.Form(
    form.Dropdown('negativeIntegrationIntervalMs', [str(i) for i in xrange(MIN_INTEGRATION_INTERVAL_MS, MAX_INTEGRATION_INTERVAL_MS, 10)], description = 'Интервал интегрирования, мс'),
    form.Dropdown('negativeIdB', [], description = 'Фаза B'),
    form.Dropdown('negativeIdC', [], description = 'Фаза C'),
    form.Checkbox('negativeAnalogEmergency', value = 'value', description = 'Запись в файл аварии'),
    form.Checkbox('negativeAnalogSelfRecorder', value = 'value', description = 'Запись в самописец'),
    form.Checkbox('negativeAnalogOpc', value = 'value', description = 'Запись в OPC'))

harmonicForm = form.Form(
    form.Dropdown('harmonicIntegrationIntervalMs', [str(i) for i in xrange(MIN_INTEGRATION_INTERVAL_MS, MAX_INTEGRATION_INTERVAL_MS, 10)], description = 'Интервал интегрирования, мс'),
    form.Dropdown('harmonicNumber', [str(i) for i in xrange(MIN_HARMONIC_NUM, MAX_HARMONIC_NUM)], description = 'Номер гармоники'),
    form.Checkbox('harmonicAnalogEmergency', value = 'value', description = 'Запись в файл аварии'),
    form.Checkbox('harmonicAnalogSelfRecorder', value = 'value', description = 'Запись в самописец'),
    form.Checkbox('harmonicAnalogOpc', value = 'value', description = 'Запись в OPC'))

activeForm = form.Form(
    form.Dropdown('activeIntegrationIntervalMs', [str(i) for i in xrange(MIN_INTEGRATION_INTERVAL_MS, MAX_INTEGRATION_INTERVAL_MS, 10)], description = 'Интервал интегрирования, мс'),
    form.Dropdown('activeIdCurrent', [], description = 'Ток'),
    form.Checkbox('activeAnalogEmergency', value = 'value', description = 'Запись в файл аварии'),
    form.Checkbox('activeAnalogSelfRecorder', value = 'value', description = 'Запись в самописец'),
    form.Checkbox('activeAnalogOpc', value = 'value', description = 'Запись в OPC'))

reactiveForm = form.Form(
    form.Dropdown('reactiveIntegrationIntervalMs', [str(i) for i in xrange(MIN_INTEGRATION_INTERVAL_MS, MAX_INTEGRATION_INTERVAL_MS, 10)], description = 'Интервал интегрирования, мс'),
    form.Dropdown('reactiveIdCurrent', [], description = 'Ток'),
    form.Checkbox('reactiveAnalogEmergency', value = 'value', description = 'Запись в файл аварии'),
    form.Checkbox('reactiveAnalogSelfRecorder', value = 'value', description = 'Запись в самописец'),
    form.Checkbox('reactiveAnalogOpc', value = 'value', description = 'Запись в OPC'))

class Analog:
    title = ''
    a = None

    def GET(self, dev, idx):
        web.header('Cache-Control', 'no-cache, must-revalidate')        
        self.title = u'Аналог ' + dev + ':' + idx

        analogFrm = analogForm()
        analogFrm.dev = dev
        analogFrm.id = idx
        a = xml['device'][dev]['analog'][idx]
        analogFrm.inUse.set_value(a['in_use'] == "yes")
        analogFrm.alias.value = a['alias']
        analogFrm.phase.value = a['phase']
        analogFrm.circuitComponent.value = a['circuit_component']
        analogFrm.ADC.set_value(a['ADC'])
        analogFrm.sinusoid.set_value(a['sinusoid'])
        analogFrm.dcComponent.set_value(a['dc_component'])
        analogFrm.coef1.set_value(a['coef1'])

        rmsFrm = rmsForm()
        if 'rms' in a.keys():
            rmsFrm.rmsIntegrationIntervalMs.set_value(a['rms']['integration_interval_ms'])
            if 'analog_emergency' in a['rms'].keys():
                rmsFrm.rmsAnalogEmergency.set_value(True)
                rmsFrm.rmsTopThreshold.set_value(a['rms']['analog_emergency']['top_threshold'])
                rmsFrm.rmsBottomThreshold.set_value(a['rms']['analog_emergency']['bottom_threshold'])
                rmsFrm.rmsMaxDuration.set_value(a['rms']['analog_emergency']['max_duration_ms'])
            if 'analog_self-recorder' in a['rms'].keys():
                rmsFrm.rmsAnalogSelfRecorder.set_value(True)
            if 'analog_opc' in a['rms'].keys():
                rmsFrm.rmsAnalogOpc.set_value(True)
        else:
            rmsFrm.rmsIntegrationIntervalMs.value = MIN_INTEGRATION_INTERVAL_MS
                rmsFrm.rmsTopThreshold.set_value('')
                rmsFrm.rmsBottomThreshold.set_value('')
                rmsFrm.rmsMaxDuration.set_value(MIN_EMERGENCY_DURATION)
            rmsFrm.rmsAnalogEmergency.set_value(False)
            rmsFrm.rmsAnalogSelfRecorder.set_value(False)
            rmsFrm.rmsAnalogOpc.set_value(False)

        zeroFrm = zeroForm() 
        if 'zero_phase_sequence' in a.keys():
            zeroFrm.zeroIntegrationIntervalMs.set_value(a['zero_phase_sequence']['integration_interval_ms'])
            if 'analog_emergency' in a['zero_phase_sequence'].keys():
                zeroFrm.zeroAnalogEmergency.set_value(True)
            if 'analog_self-recorder' in a['zero_phase_sequence'].keys():
                zeroFrm.zeroAnalogSelfRecorder.set_value(True)
            if 'analog_opc' in a['zero_phase_sequence'].keys():
                zeroFrm.zeroAnalogOpc.set_value(True)
        else:
            zeroFrm.zeroIntegrationIntervalMs.value = MIN_INTEGRATION_INTERVAL_MS
            zeroFrm.zeroAnalogEmergency.set_value(False)
            zeroFrm.zeroAnalogSelfRecorder.set_value(False)
            zeroFrm.zeroAnalogOpc.set_value(False)

        positiveFrm = positiveForm() 
        if 'positive_phase_sequence' in a.keys():
            positiveFrm.positiveIntegrationIntervalMs.set_value(a['positive_phase_sequence']['integration_interval_ms'])
            if 'analog_emergency' in a['positive_phase_sequence'].keys():
                positiveFrm.positiveAnalogEmergency.set_value(True)
            if 'analog_self-recorder' in a['positive_phase_sequence'].keys():
                positiveFrm.positiveAnalogSelfRecorder.set_value(True)
            if 'analog_opc' in a['positive_phase_sequence'].keys():
                positiveFrm.positiveAnalogOpc.set_value(True)
        else:
            positiveFrm.positiveIntegrationIntervalMs.value = MIN_INTEGRATION_INTERVAL_MS
            positiveFrm.positiveAnalogEmergency.set_value(False)
            positiveFrm.positiveAnalogSelfRecorder.set_value(False)
            positiveFrm.positiveAnalogOpc.set_value(False)

        negativeFrm = negativeForm() 
        if 'negative_phase_sequence' in a.keys():
            negativeFrm.negativeIntegrationIntervalMs.set_value(a['negative_phase_sequence']['integration_interval_ms'])
            if 'analog_emergency' in a['negative_phase_sequence'].keys():
                negativeFrm.negativeAnalogEmergency.set_value(True)
            if 'analog_self-recorder' in a['negative_phase_sequence'].keys():
                negativeFrm.negativeAnalogSelfRecorder.set_value(True)
            if 'analog_opc' in a['negative_phase_sequence'].keys():
                negativeFrm.negativeAnalogOpc.set_value(True)
        else:
            negativeFrm.negativeIntegrationIntervalMs.value = MIN_INTEGRATION_INTERVAL_MS
            negativeFrm.negativeAnalogEmergency.set_value(False)
            negativeFrm.negativeAnalogSelfRecorder.set_value(False)
            negativeFrm.negativeAnalogOpc.set_value(False)

        harmonicFrm = harmonicForm() 
        if 'harmonic' in a.keys():
            harmonicFrm.harmonicIntegrationIntervalMs.set_value(a['harmonic']['integration_interval_ms'])
            harmonicFrm.harmonicNumber(a['harmonic']['number'])
            if 'analog_emergency' in a['harmonic'].keys():
                harmonicFrm.harmonicAnalogEmergency.set_value(True)
            if 'analog_self-recorder' in a['harmonic'].keys():
                harmonicFrm.harmonicAnalogSelfRecorder.set_value(True)
            if 'analog_opc' in a['harmonic'].keys():
                harmonicFrm.harmonicAnalogOpc.set_value(True)
        else:
            harmonicFrm.harmonicIntegrationIntervalMs.value = MIN_INTEGRATION_INTERVAL_MS
            harmonicFrm.harmonicNumber = MIN_HARMONIC_NUM
            harmonicFrm.harmonicAnalogEmergency.set_value(False)
            harmonicFrm.harmonicAnalogSelfRecorder.set_value(False)
            harmonicFrm.harmonicAnalogOpc.set_value(False)

        activeFrm = activeForm() 
        if 'active_power' in a.keys():
            activeFrm.activeIntegrationIntervalMs.set_value(a['active_power']['integration_interval_ms'])
            activeFrm.activeIdCurrent.set_value(a['active_power']['id_current'])
            if 'analog_emergency' in a['active_power'].keys():
                activeFrm.activeAnalogEmergency.set_value(True)
            if 'analog_self-recorder' in a['active_power'].keys():
                activeFrm.activeAnalogSelfRecorder.set_value(True)
            if 'analog_opc' in a['active_power'].keys():
                activeFrm.activeAnalogOpc.set_value(True)
        else:
            activeFrm.activeIntegrationIntervalMs.value = MIN_INTEGRATION_INTERVAL_MS
            activeFrm.activeIdCurrent = ''
            activeFrm.activeAnalogEmergency.set_value(False)
            activeFrm.activeAnalogSelfRecorder.set_value(False)
            activeFrm.activeAnalogOpc.set_value(False)

        reactiveFrm = reactiveForm() 
        if 'reactive_power' in a.keys():
            reactiveFrm.reactiveIntegrationIntervalMs.set_value(a['reactive_power']['integration_interval_ms'])
            reactiveFrm.reactiveIdCurrent.set_value(a['reactive_power']['id_current'])
            if 'analog_emergency' in a['reactive_power'].keys():
                reactiveFrm.reactiveAnalogEmergency.set_value(True)
            if 'analog_self-recorder' in a['reactive_power'].keys():
                reactiveFrm.reactiveAnalogSelfRecorder.set_value(True)
            if 'analog_opc' in a['reactive_power'].keys():
                reactiveFrm.reactiveAnalogOpc.set_value(True)
        else:
            reactiveFrm.reactiveIntegrationIntervalMs.value = MIN_INTEGRATION_INTERVAL_MS
            reactiveFrm.reactiveIdCurrent = ''
            reactiveFrm.reactiveAnalogEmergency.set_value(False)
            reactiveFrm.reactiveAnalogSelfRecorder.set_value(False)
            reactiveFrm.reactiveAnalogOpc.set_value(False)

        return render.analog(analogFrm, rmsFrm, zeroFrm, positiveFrm, negativeFrm, harmonicFrm, activeFrm, reactiveFrm, title = self.title)

    def setHandlers(self, filtr, emg, rec, opc):
        if filtr not in self.a.keys():
            self.a[filtr] = {}
        for nv, ov in zip((emg, rec, opc), ('analog_emergency', 'analog_self-recorder', 'analog_opc')):
            if nv:
                self.a[filtr][ov] = {}
            elif ov in self.a[filtr].keys():
                self.a[filtr].pop(ov)

    def POST(self, dev, idx):
        analogFrm = analogForm()
        analogFrm.dev = dev
        analogFrm.id = idx
        rmsFrm = rmsForm()
        zeroFrm = zeroForm()
        positiveFrm = positiveForm()
        negativeFrm = negativeForm()
        harmonicFrm = harmonicForm()
        activeFrm = activeForm()
        reactiveFrm = reactiveForm()

        valid = analogFrm.validates()
        rmsValid = rmsFrm.validates()
        zeroValid = zeroFrm.validates()
        positiveValid = positiveFrm.validates()
        negativeValid = negativeFrm.validates()
        harmonicValid = harmonicFrm.validates()
        activeValid = activeFrm.validates()
        reactiveValid = reactiveFrm.validates()
        valid = valid and rmsValid and positiveValid and \
            negativeValid and harmonicValid and activeValid and \
            reactiveValid
        if not valid:
            return render.analog(analogFrm, rmsFrm, zeroFrm, positiveFrm, negativeFrm, harmonicFrm, activeFrm, reactiveFrm, title = self.title)

        self.a = xml['device'][dev]['analog'][idx]
        
        inUse = 'no'
        if analogFrm.inUse.get_value():
            inUse = 'yes'
        self.a['in_use'] = inUse
        self.a['alias'] = analogFrm.alias.value
        self.a['phase'] = analogFrm.phase.value
        self.a['circuit_component'] = analogFrm.circuitComponent.value
        self.a['ADC'] = analogFrm.ADC.get_value()
        self.a['sinusoid'] = analogFrm.sinusoid.get_value()
        self.a['dc_component'] = analogFrm.dcComponent.value
        self.a['coef1'] = analogFrm.coef1.get_value()
        #rms 
        emg = rmsFrm.rmsAnalogEmergency.get_value()
        rec = rmsFrm.rmsAnalogSelfRecorder.get_value()
        opc = rmsFrm.rmsAnalogOpc.get_value()
        self.setHandlers('rms', emg, rec, opc)
        self.a['rms']['integration_interval_ms'] = rmsFrm.rmsIntegrationIntervalMs.get_value()

        #zero phase sequence
        emg = zeroFrm.zeroAnalogEmergency.get_value()
        rec = zeroFrm.zeroAnalogSelfRecorder.get_value()
        opc = zeroFrm.zeroAnalogOpc.get_value()
        self.setHandlers('zero_phase_sequence', emg, rec, opc)
        self.a['zero_phase_sequence']['integration_interval_ms'] = zeroFrm.zeroIntegrationIntervalMs.get_value()

        #positive phase sequence
        emg = positiveFrm.positiveAnalogEmergency.get_value()
        rec = positiveFrm.positiveAnalogSelfRecorder.get_value()
        opc = positiveFrm.positiveAnalogOpc.get_value()
        self.setHandlers('positive_phase_sequence', emg, rec, opc)
        self.a['positive_phase_sequence']['integration_interval_ms'] = positiveFrm.positiveIntegrationIntervalMs.get_value()
        
        #negative phase sequence
        emg = negativeFrm.negativeAnalogEmergency.get_value()
        rec = negativeFrm.negativeAnalogSelfRecorder.get_value()
        opc = negativeFrm.negativeAnalogOpc.get_value()
        self.setHandlers('negative_phase_sequence', emg, rec, opc)
        self.a['negative_phase_sequence']['integration_interval_ms'] = negativeFrm.negativeIntegrationIntervalMs.get_value()
        
        #harmonic
        emg = harmonicFrm.harmonicAnalogEmergency.get_value()
        rec = harmonicFrm.harmonicAnalogSelfRecorder.get_value()
        opc = harmonicFrm.harmonicAnalogOpc.get_value()
        self.setHandlers('harmonic', emg, rec, opc)
        self.a['harmonic']['integration_interval_ms'] = harmonicFrm.harmonicIntegrationIntervalMs.get_value()
        self.a['harmonic']['number'] = harmonicFrm.harmonicNumber.get_value()
        
        #active power
        emg = activeFrm.activeAnalogEmergency.get_value()
        rec = activeFrm.activeAnalogSelfRecorder.get_value()
        opc = activeFrm.activeAnalogOpc.get_value()
        self.setHandlers('active_power', emg, rec, opc)
        self.a['active_power']['integration_interval_ms'] = activeFrm.activeIntegrationIntervalMs.get_value()
        self.a['active_power']['id_current'] = activeFrm.activeIdCurrent.get_value()
        
        #reactive power
        emg = reactiveFrm.reactiveAnalogEmergency.get_value()
        rec = reactiveFrm.reactiveAnalogSelfRecorder.get_value()
        opc = reactiveFrm.reactiveAnalogOpc.get_value()
        self.setHandlers('reactive_power', emg, rec, opc)
        self.a['reactive_power']['integration_interval_ms'] = reactiveFrm.reactiveIntegrationIntervalMs.get_value()
        self.a['reactive_power']['id_current'] = reactiveFrm.reactiveIdCurrent.get_value()
      
        #Постоянный ток
        if self.a['sinusoid'] == 'no':
            note = 'Неприменимо для постоянного тока'
            if 'analog_emergency' in self.a['zero_phase_sequence'].keys():
                zeroFrm.zeroAnalogEmergency.note = note
                valid = False
            if 'analog_self-recorder' in self.a['zero_phase_sequence'].keys():
                zeroFrm.zeroAnalogSelfRecorder.note = note
                valid = False
            if 'analog_opc' in self.a['zero_phase_sequence'].keys():
                zeroFrm.zeroAnalogOpc.note = note
                valid = False
            if 'analog_emergency' in self.a['positive_phase_sequence'].keys():
                positiveFrm.positiveAnalogEmergency.note = note
                valid = False
            if 'analog_self-recorder' in self.a['positive_phase_sequence'].keys():
                positiveFrm.positiveAnalogSelfRecorder.note = note
                valid = False
            if 'analog_opc' in self.a['positive_sequence'].keys():
                zeroFrm.zeroAnalogOpc.note = note
                valid = False
            if 'analog_emergency' in self.a['negative_phase_sequence'].keys():
                negativeFrm.negativeAnalogEmergency.note = note
                valid = False
            if 'analog_self-recorder' in self.a['negative_phase_sequence'].keys():
                negativeFrm.negativeAnalogSelfRecorder.note = note
                valid = False
            if 'analog_opc' in self.a['negative_phase_sequence'].keys():
                negativeFrm.negativeAnalogOpc.note = note
                valid = False
            if 'analog_emergency' in self.a['harmonic'].keys():
                harmonicFrm.harmonicAnalogEmergency.note = note
                valid = False
            if 'analog_self-recorder' in self.a['harmonic'].keys():
                harmonicFrm.harmonicAnalogSelfRecorder.note = note
                valid = False
            if 'analog_opc' in self.a['harmonic'].keys():
                harmonicFrm.harmonicAnalogOpc.note = note
                valid = False
            if 'analog_emergency' in self.a['active_power'].keys():
                activeFrm.activeAnalogEmergency.note = note
                valid = False
            if 'analog_self-recorder' in self.a['active_power'].keys():
                activeFrm.activeAnalogSelfRecorder.note = note
                valid = False
            if 'analog_opc' in self.a['active_power'].keys():
                activeFrm.activeAnalogOpc.note = note
                valid = False
            if 'analog_emergency' in self.a['reactive_power'].keys():
                reactiveFrm.reactiveAnalogEmergency.note = note
                valid = False
            if 'analog_self-recorder' in self.a['reactive_power'].keys():
                reaciveFrm.reactiveAnalogSelfRecorder.note = note
                valid = False
            if 'analog_opc' in self.a['reactive_power'].keys():
                reactiveFrm.reactiveAnalogOpc.note = note
                valid = False

        if not valid:
            return render.analog(analogFrm, rmsFrm, zeroFrm, positiveFrm, negativeFrm, harmonicFrm, activeFrm, reactiveFrm, title = self.title)
        
        
        xml['device'][dev]['analog'][idx] = self.a
        print xmlRender(xml)
        return render.completion(self.title)
