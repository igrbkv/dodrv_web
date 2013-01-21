# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender, rewriteConfigXml
import math
from utils import restart_service

MIN_INTEGRATION_INTERVAL_MS = 10
MAX_INTEGRATION_INTERVAL_MS = 100
MIN_HARMONIC_NUM = 1
MAX_HARMONIC_NUM = 20
MIN_EMERGENCY_DURATION = 0
ADC_MULTIPLICATOR = 10.

FLOAT_REGEXP = '([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)|^$'
MUST_BE_NUMBER_NOTE = 'Должно быть число'
COEF1_NOTE = 'Должно быть число не меньшее 1.'
MUST_BE_POSITIVE_NUMBER_NOTE = 'Должно быть число не меньшее 0.'
UNUSABLE_FOR_DC_NOTE = 'Неприменимо для постоянного тока'
THRESHOLD_TOO_BIG_NOTE = 'Значение превышает порог измерения: %f'
THRESHOLDS_INTERSECTION_NOTE = 'Пересечение с порогом по понижению недопустимо'
THRESHOLDS_EMPTY_NOTE = 'Не заданы пороги'
EMPTY_VALUE_NOTE = 'Значение не задано'
INVALID_FLT_PARMS_NOTE = 'Неприменимо. Неверные параметры фильтра'
PHASES_B_C_MUST_BE_DIF_NOTE = 'Сигналы фаз В и С должны быть разные'

analogForm = form.Form(
    form.Checkbox('in_use', value = 'value', checked = True, description = 'Используется'),
    form.Textbox('alias', description = 'Имя'),
    form.Dropdown('phase', ['', 'A', 'B', 'C'], description = 'Фаза'),
    form.Textbox('circuit_component', description = 'Элемент цепи'),
    form.Dropdown('ADC', [adc for adc in xml['ADCs'].keys()], description = 'ADC'),
    form.Dropdown('sinusoid', [('yes', '~'), ('no','-')], description = 'Ток'),
    form.Textbox('dc_component', 
        form.Validator(MUST_BE_NUMBER_NOTE, bool),
        form.regexp(FLOAT_REGEXP, MUST_BE_NUMBER_NOTE),
        description = 'Пост. составляющая, В или А'),
    form.Textbox('coef1', 
        form.Validator(COEF1_NOTE, bool),
        form.regexp(FLOAT_REGEXP, COEF1_NOTE),
        form.Validator(COEF1_NOTE, lambda i: float(i) >= 1.0),
        description = 'Коэффициент преобраз. из первичных цепей'))

def createForm(pref, dev = None, idx = None):
    pref_ = pref + '_'
    inputs = [] 
    #Общее 1 
    inputs.append(form.Dropdown(pref_ + 'integration_interval_ms', 
        [str(i) for i in xrange(MIN_INTEGRATION_INTERVAL_MS, MAX_INTEGRATION_INTERVAL_MS, 10)], 
        description = 'Интервал интегрирования, мс'))

    #Индивидуальное
    if pref in ('zero_phase_sequence', 'positive_phase_sequence', 'negative_phase_sequence'):
        analogs = xml['device'][dev]['analog']
        adc = analogs[idx]['ADC']
        ps = [a['id'] for a in analogs.values() 
            if a['ADC'] == adc and a['id'] != idx]
        ps = sorted(ps, cmp = lambda x, y: cmp(int(x), int(y)))

        inputs += (form.Dropdown(pref_ + 'id_b', ps, description = 'Фаза B'),
            form.Dropdown(pref_ +'id_c', ps, description = 'Фаза C'))
    elif pref == 'harmonic': 
        inputs.append(form.Dropdown(pref_ + 'number', [str(i) for i in xrange(MIN_HARMONIC_NUM, MAX_HARMONIC_NUM)], description = 'Номер гармоники'))
    elif pref in ('active_power', 'reactive_power'):
        analogs = xml['device'][dev]['analog']
        adcs = [k for k, v in xml['ADCs'].iteritems() if v['unit'] == 'A']
        ps = [a['id'] for a in analogs.values()
            if a['ADC'] in adcs]
        ps = sorted(ps, cmp = lambda x, y: cmp(int(x), int(y)))

        inputs.append(form.Dropdown(pref_ + 'id_current', ps, description = 'Ток'))

    #Общее 2
    inputs += (form.Checkbox(pref_ + 'analog_emergency', value = 'value', description = 'Запись в файл аварии'),
        form.Textbox(pref_ + 'top_threshold', 
        form.regexp(FLOAT_REGEXP, MUST_BE_POSITIVE_NUMBER_NOTE),
            description = 'Верхняя граница'),
        form.Textbox(pref_ + 'bottom_threshold', 
            form.regexp(FLOAT_REGEXP, MUST_BE_POSITIVE_NUMBER_NOTE),
            description = 'Нижняя граница'),
        form.Dropdown(pref_ + 'max_duration_s', ['1', '3', '5', '10', '30'], description = 'Макс. длительность регистрации, с'),
        form.Checkbox(pref_ + 'analog_self-recorder', value = 'value', description = 'Запись в самописец'),
        form.Textbox(pref_ + 'analog_delta_percent', 
            form.regexp(FLOAT_REGEXP, MUST_BE_POSITIVE_NUMBER_NOTE),
            description = 'Процент изменения'),
        form.Checkbox(pref_ + 'analog_opc', value = 'value', description = 'Запись в OPC'))

    return form.Form(*inputs)

class Analog:
    title = ''
    a = None

    def setForm(self, pref, frm):
        pref_ = pref + '_'
        if pref in self.a.keys():
            pars = ['integration_interval_ms']
            if pref in ('zero_phase_sequence', 'positive_phase_sequence', 'negative_phase_sequence'):
                pars += ('id_b', 'id_c')
            elif pref == 'harmonic':
                pars.append('number')
            elif pref in ('active_power', 'reactive_power'):
                pars.append('id_current') 
            for par in pars:
                frm[pref_ + par].set_value(self.a[pref][par])
            for par in ('analog_emergency', 'analog_self-recorder', 'analog_opc'):
                if par in self.a[pref].keys():
                    frm[pref_+ par].set_value(True)
                    for k in self.a[pref][par].keys():
                        frm[pref_ + k].set_value(self.a[pref][par][k])
        return frm

    def getForm(self, pref, frm):
        pref_ = pref + '_'
        handlers = [h for h in ('analog_emergency', 'analog_self-recorder', 'analog_opc')
            if frm[pref_ + h].get_value()]
        #Удалить старые данные
        if pref in self.a.keys():
            self.a.pop(pref)
        if handlers:
            #Параметры фильтра
            self.a[pref] = {}
            keys = ['integration_interval_ms']
            if pref in ('zero_phase_sequence', 'positive_phase_sequence', 'negative_phase_sequence'):
                keys += ('id_b', 'id_c')
            elif pref == 'harmonic':
                keys.append('number')
            elif pref in ('active_power', 'reactive_power'):
                keys.append('id_current')
            for k in keys:
                self.a[pref][k] = frm[pref_ + k].get_value()
                if self.a[pref][k]: self.a[pref][k].strip()
            #Параметры обработчиков
            for h in handlers:
                self.a[pref][h] = {}
                keys = []
                if h == 'analog_emergency':
                    keys += ('bottom_threshold', 'top_threshold', 'max_duration_s')
                elif h == 'analog_self-recorder':
                    keys.append('analog_delta_percent')
                for k in keys:
                    self.a[pref][h][k] = frm[pref_ + k].get_value()
                    if self.a[pref][h][k]: self.a[pref][h][k].strip()

    def _commonCheck(self, pref, frm, dev = None):
        if pref not in self.a.keys():
            return frm, True
        valid = True
        pref_ = pref + '_'
        note = INVALID_FLT_PARMS_NOTE
        handlers = [h for h in ('analog_emergency', 'analog_self-recorder', 'analog_opc')
            if h in self.a[pref].keys()]
        if handlers:
            #Проверка фильтров
            if self.a['sinusoid'] == 'no' and pref in ('zero_phase_sequence', 
                'positive_phase_sequence', 'negative_phase_sequence', 
                'harmonic', 'active_power', 'reactive_power'):
                note = UNUSABLE_FOR_DC_NOTE
                valid = False
            else:
                if pref in ('zero_phase_sequence', 'positive_phase_sequence', 'negative_phase_sequence'):
                    if not self.a[pref]['id_b'] or not self.a[pref]['id_c']:
                        valid = False
                    elif self.a[pref]['id_b'] == self.a[pref]['id_c']:
                        frm[pref_ + 'id_c'].note = PHASES_B_C_MUST_BE_DIF_NOTE
                        valid = False
                elif pref in ('active_power', 'reactive_power'):
                    if not self.a[pref]['id_current']:
                        valid = False
                    elif xml['ADCs'][self.a['ADC']]['unit'] == xml['ADCs'][xml['device'][dev]['analog'][self.a[pref]['id_current']]['ADC']]['unit']:
                        valid = False
            if not  valid:
                for h in handlers:
                    frm[pref_ + h].note = note
                return frm, valid

            #Проверка обработчиков
            par = 'analog_emergency'
            if par in handlers:
                bottom = self.a[pref][par]['bottom_threshold']
                top = self.a[pref][par]['top_threshold']
                if bottom or top:
                    if bottom and top and float(bottom) >= float(top):
                        frm[pref_ + 'bottom_threshold'].note = THRESHOLDS_INTERSECTION_NOTE
                        valid = False
                    if top:
                        topBound = ADC_MULTIPLICATOR*float(xml['ADCs'][self.a['ADC']]['coef2'])*float(self.a['coef1'])
                        if pref in ('rms', 'harmonic'):
                            if self.a['sinusoid'] == 'yes':
                                topBound /= math.sqrt(2)
                        elif pref in ('zero_phase_sequence', 'positive_phase_sequence', 'negative_phase_sequence'):
                            topBound *= 3
                        elif pref in ('active_power', 'reactive_power'):
                            aI = xml['device'][dev]['analog'][self.a[pref]['id_current']]
                            topBound *= ADC_MULTIPLICATOR*float(xml['ADCs'][aI['ADC']]['coef2'])*float(aI['coef1'])/2

                        if topBound  < float(top):
                            frm[top].note = THRESHOLD_TOO_BIG_NOTE % topBound
                            valid = False
                else:
                    frm[pref_ + par].note = THRESHOLDS_EMPTY_NOTE
                    valid = False

            par = 'analog_self-recorder'
            if par in handlers and not self.a[pref][par]['analog_delta_percent']:
                frm[pref_ + 'analog_delta_percent'].note = EMPTY_VALUE_NOTE

        return frm, valid

    def GET(self, dev, idx):
        web.header('Content-Type', 'text/html; charset= utf-8')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')
        self.title = u'Аналог ' + dev + ':' + idx
        self.a = xml['device'][dev]['analog'][idx]

        analogFrm = analogForm()
        analogFrm.dev = dev
        analogFrm.id = idx
        analogFrm['in_use'].set_value(self.a['in_use'] == "yes")
        for k in ('alias', 'phase', 'circuit_component', 'ADC', 'sinusoid', 'dc_component', 'coef1'):
            analogFrm[k].set_value(self.a[k])

        par = 'rms'
        rmsFrm = self.setForm(par, createForm(par))
        par = 'zero_phase_sequence'
        zeroFrm = self.setForm(par, createForm(par, dev, idx))
        par = 'positive_phase_sequence'
        positiveFrm = self.setForm(par, createForm(par, dev, idx))
        par = 'negative_phase_sequence'
        negativeFrm = self.setForm(par, createForm(par, dev, idx))
        par = 'harmonic'
        harmonicFrm = self.setForm(par, createForm(par, dev, idx))
        par = 'active_power'
        activeFrm = self.setForm(par, createForm(par, dev, idx))
        par = 'reactive_power'
        reactiveFrm = self.setForm(par, createForm(par, dev, idx))

        return render.analog(analogFrm, rmsFrm, zeroFrm, positiveFrm, negativeFrm, harmonicFrm, activeFrm, reactiveFrm, title = self.title)

    def POST(self, dev, idx):
        analogFrm = analogForm()
        analogFrm.dev = dev
        analogFrm.id = idx
        rmsFrm = createForm('rms')
        zeroFrm = createForm('zero_phase_sequence', dev, idx)
        positiveFrm = createForm('positive_phase_sequence', dev, idx)
        negativeFrm = createForm('negative_phase_sequence', dev, idx)
        harmonicFrm = createForm('harmonic')
        activeFrm = createForm('active_power', dev, idx)
        reactiveFrm = createForm('reactive_power', dev, idx)

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
        
        in_use = 'no'
        if analogFrm.in_use.get_value():
            in_use = 'yes'
        self.a['in_use'] = in_use
        for k in ('alias', 'phase', 'circuit_component', 'ADC', 'sinusoid', 'dc_component', 'coef1'):
            self.a[k] = analogFrm[k].get_value()

        self.getForm('rms', rmsFrm)
        self.getForm('zero_phase_sequence', zeroFrm)
        self.getForm('positive_phase_sequence', positiveFrm)
        self.getForm('negative_phase_sequence', negativeFrm)
        self.getForm('harmonic', harmonicFrm)
        self.getForm('active_power', activeFrm)
        self.getForm('reactive_power', reactiveFrm)
     
        #Общая проверка
        rmsFrm, rmsValid = self._commonCheck('rms', rmsFrm)
        zeroFrm, zeroValid = self._commonCheck('zero_phase_sequence', zeroFrm)
        positiveFrm, positiveValid = self._commonCheck('positive_phase_sequence', positiveFrm)
        negativeFrm, negativeValid = self._commonCheck('negative_phase_sequence', negativeFrm)
        harmonicFrm, harmonicValid = self._commonCheck('harmonic', harmonicFrm)
        activeFrm, activeValid = self._commonCheck('active_power', activeFrm, dev)
        reactiveFrm, reactiveValid = self._commonCheck('reactive_power', reactiveFrm, dev)
        if not (rmsValid and zeroValid and positiveValid and negativeValid and harmonicValid and activeFrm and reactiveFrm):
            return render.analog(analogFrm, rmsFrm, zeroFrm, positiveFrm, negativeFrm, harmonicFrm, activeFrm, reactiveFrm, title = self.title)
        
        xml['device'][dev]['analog'][idx] = self.a
        
        rewriteConfigXml()
        restart_service('dofilters.pov' + str(dev))

        return render.completion(self.title)
