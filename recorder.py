# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender, rewriteConfigXml, MAX_POV, DEBUG_PATH
from os import path
from utils import restart_service
from http import nocache
from subprocess import call

HOSTNAME_PATH=DEBUG_PATH + '/etc/conf.d/hostname'

signals = [u'16 аналогов 32 дискрета', u'128 дискрет']
comtradeFormats = ['COMTRADE ASCII', 'COMTRADE BIN']
notes = (
    '* Должно быть число от 0 до 99', 
    '* Должно быть число 0 до 60', 
    '* Должно быть число от 0.0 до 100.0')

recorderForm = form.Form(
    form.Textbox('station_name', description = 'Энергообъект'),
    form.Textbox(
        'id', 
        form.Validator(notes[0], bool),
        form.regexp('\d+', notes[0]),
        form.Validator(notes[0], lambda i: int(i) >= 0 and int(i) < 100),
        description = 'Идентификатор'),
    form.Dropdown('type', [xml['type'],], description = 'Тип'))

def createPovForms():
    pf = {}
    for i in xrange(MAX_POV):
        if xml['device'].has_key(str(i)) and xml['device'][str(i)]['exists']:
            p = form.Form(
                form.Checkbox('pov%d' % i, value = '%d' % i, 
                    description = 'Канал %d' % i),
                form.Dropdown('signals%d' % i, signals, description = ''))
            pf[i] = p
    return pf

povForms = createPovForms()

emergencyForm = form.Form(
    form.Dropdown('prehistory_ms', ['0', '100', '200', '500', '1000'], description = 'Предыстория (мс)'),
    form.Dropdown('after_history_ms', ['0', '100', '500', '1000', '5000', '10000'], description = 'Послеистория (мс)'),
    #FIXME Не реализовано в emergencyfile.cpp
    #form.Textbox('max_file_length_s',  
    #    form.Validator(notes[1], bool),
    #    form.regexp('\d+', notes[1]),
    #    form.Validator(notes[1], lambda i: int(i) >= 0 and int(i) <= 60),
    #    description = 'Макс. длина файла аварии (с)'),
    form.Dropdown('keeping_period_days', ['1', '3', '8', '30', '60'], description = 'Макс.время хранения (дней)'))

selfRecorderForm = form.Form(
    form.Dropdown('live_update_ms', ['1000', '2000', '5000', '10000'], description = 'Контрольный период записи(мс)'),
    form.Textbox('analog_delta_percent', 
        form.Validator(notes[2], bool),
        form.regexp('\d+[.\d*]{0,1}', notes[2]),
        form.Validator(notes[2], lambda v: float(v) >= .0 and float(v) <= 100.),
        description = 'Порог изменения (%)'), 
    form.Dropdown('max_file_length_hour', ['1', '2', '3', '6', '12'], description = 'Макс.длина файла (час)'),
    form.Dropdown('keeping_time_days', ['1', '3', '8', 15], description = 'Макс.время хранения (дней)'))
    
formatForm = form.Form(
    form.Dropdown('format', comtradeFormats, description = 'Формат файлов данных'),
    form.Dropdown('codeset', ['CP1251',], description = 'Кодировка'),
)

def setDevSigNum(dev, aNew, dNew):
    """16 analogs 32 discretes <=> 128 discrets"""
    aOld = xml['device'][dev]['analogs']
    dOld = xml['device'][dev]['discretes']
    if aNew != aOld: 
        if aNew == '0':
            xml['device'][dev]['analog'] = {}
        else:
            tmpl = {
                'in_use': 'no', 
                'coef1':'1.0', 
                'ADC': xml['ADCs'].keys()[0], #Первый попавшийся
                'dc_component':'0', 
                'sinusoid': 'yes', 
                'alias=': '', 
                'phase': '',
                'filters':{}}
            xml['device'][dev]['analog'] = dict((str(ii), tmpl) for ii in xrange(int(aNew)))
    if dNew != dOld:
        if dNew == '32':
            for ii in xrange(32, 128):
                xml['device'][dev]['discrete'].pop(str(ii))
        else:
            tmpl = {
                'in_use': 'yes', 
                'inverted': 'yes',
                'alias': '',
                'phase': '',
                'circuit_component': '',
                'filters':{}}
            for ii in xrange(32, 128):
                xml['device'][dev][str(ii)] = tmpl
    xml['device'][dev]['analogs'] = aNew
    xml['device'][dev]['discretes'] = dNew


class Recorder:
    """
    """
    title = 'Параметры регистратора'


    def GET(self):
        nocache()
        
        rf = recorderForm()
        for k in ('id', 'station_name'):
            rf[k].value = xml[k] 
        
        pfs = povForms
        for i in pfs.keys():
            getattr(pfs[i], 'pov%d' % i).set_value(xml['device'][str(i)]['in_use'] == "yes")
            si = 0
            if xml['device'][str(i)]['discretes'] == '128': 
                si = 1
            getattr(pfs[i], 'signals%d' % i).value = signals[si]
        
        ef = emergencyForm()
        par = 'emergency'
        for k in ('prehistory_ms', 'after_history_ms', 'keeping_period_days'):
            ef[k].value = xml[par][k] 
        #FIXME Не реализовано в emergencyfile.cpp
        #ef.max_file_length_s.value = str(int(xml['emergency']['max_file_length_s']))

        sf = selfRecorderForm()
        par = 'self-recorder'
        for k in ('live_update_ms', 'analog_delta_percent', 'max_file_length_hour', 'keeping_time_days'):
            sf[k].value = xml[par][k] 
        
        ff = formatForm()
        if xml['data_formats']['choice'] == 'comtrade':
            ff.codeset.value = xml['data_formats']['comtrade']['codeset']
            fi = 0
            if xml['data_formats']['comtrade']['data_file'] == 'BIN': 
                fi = 1
            ff.format.value = comtradeFormats[fi]

        return render.recorder(rf, pfs, ef, sf, ff, self.title)

    def POST(self):
        valid = True
        rf = recorderForm()
        pfs = povForms
        ef = emergencyForm()
        sf = selfRecorderForm()
        ff = formatForm()
        
        valid &= rf.validates()
        for i in pfs.keys():
            pfs[i].validates()
        valid &= ef.validates() 
        valid &= sf.validates() 
        valid &= ff.validates()

        if not valid:
            return render.recorder(rf, pfs, ef, sf, ff, self.title)
        #Запись парметров
        for k in ('id', 'station_name'):
            xml[k] = rf[k].value
        
        for i in pfs.keys():
            inUse = 'yes'
            if not getattr(pfs[i], 'pov%d' % i).get_value():
                inUse = 'no'
            xml['device'][str(i)]['in_use'] = inUse

            a, d = '0', '128'
            if getattr(pfs[i], 'signals%d' % i).value == signals[0]:
                a, d = '16', '32'
            setDevSigNum(str(i), a, d)
        
        par = 'emergency'
        for k in ('prehistory_ms', 'after_history_ms', 'keeping_period_days'):
            xml[par][k] = ef[k].value
        #FIXME Не реализовано в emergencyfile.cpp
        #xml[par]['max_file_length_s'] = str(int(ef.max_file_length_s.value))

        par = 'self-recorder'
        for k in ('live_update_ms', 'analog_delta_percent', 'max_file_length_hour', 'keeping_time_days'):
            xml[par][k] = sf[k].value

        xml['data_formats']['comtrade']['codeset'] = ff.codeset.value
        f = 'BIN'
        if ff.format.value == comtradeFormats[0]:
            f = 'ASCII'
        xml['data_formats']['comtrade']['data_file'] = f
       
        with open(HOSTNAME_PATH, 'w') as hf:
            hn='r%s' % xml['id']
            hf.write('HOSTNAME="%s"\n' % hn)
        call(['hostname', hn])
        rewriteConfigXml()
        for k in xml['device'].iterkeys():
            # str(k) necessarily
            restart_service('dofilters.pov'+ str(k))
        
        return render.completion(self.title, 'Данные записаны')

