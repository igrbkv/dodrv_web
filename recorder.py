# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender

signals = [u'16 аналогов 32 дискрета', u'128 дискрет']
comtradeFormats = ['COMTRADE ASCII', 'COMTRADE BIN']
notes = (
    '* Должно быть число от 0 до 99', 
    '* Должно быть число 0 до 60', 
    '* Должно быть число от 0.0 до 100.0')

recorderForm = form.Form(
    form.Textbox(
        'id', 
        form.Validator(notes[0], bool),
        form.regexp('\d+', notes[0]),
        form.Validator(notes[0], lambda i: int(i) >= 0 and int(i) < 100),
        description = 'Идентификатор'),
    form.Textbox('name', description = 'Имя регистратора'),
    form.Textbox('stationName', description = 'Энергообъект'),
    form.Dropdown('type', [xml['type'],], description = 'Тип'))

def createPovForms():
    pf = []
    for i in xrange(len(xml['device'])):
        p = form.Form(
            form.Checkbox('pov%s' % i, value = '%s' %i, description = 'Канал %s' % i),
            form.Dropdown('signals%s' % i, signals, description = ''))
        pf.append(p)
    return pf

povForms = createPovForms()

emergencyForm = form.Form(
    form.Dropdown('prehistoryMs', ['0', '100', '200', '500', '1000'], description = 'Предыстория (мс)'),
    form.Dropdown('afterHistoryMs', ['0', '100', '500', '1000', '5000', '10000'], description = 'Послеистория (мс)'),
    form.Textbox('maxFileLengthS',  
        form.Validator(notes[1], bool),
        form.regexp('\d+', notes[1]),
        form.Validator(notes[1], lambda i: int(i) >= 0 and int(i) <= 60),
        description = 'Макс. длина файла аварии (с)'),
    form.Dropdown('maxStorageTimeDay', ['0', '1', '3', '8', '30', '60'], description = 'Макс.время хранения (дней)'))

selfRecorderForm = form.Form(
    form.Dropdown('liveUpdateMs', ['1000', '2000', '5000', '10000'], description = 'Контрольный период записи(мс)'),
    form.Textbox('analogDeltaPercent', 
        form.Validator(notes[2], bool),
        form.regexp('\d+[.\d*]{0,1}', notes[2]),
        form.Validator(notes[2], lambda v: float(v) >= .0 and float(v) <= 100.),
        description = 'Порог изменения (%)'), 
    form.Dropdown('maxFileLengthHour', ['1', '2', '3', '6', '12'], description = 'Макс.длина файла (час)'),
    form.Dropdown('maxSelfRecStorageTimeDay', ['0', '1', '3', '8'], description = 'Макс.время хранения (дней)'))
    
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
                'harmonic': 'yes', 
                'alias=': '', 
                'phase': '',
                'filters':{}}
            xml['device'][dev]['analogs'] = dict((str(ii), tmpl) for ii in xrange(int(aNew)))
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

    def POST(self):
        valid = True
        rf = recorderForm()
        pfs = povForms
        ef = emergencyForm()
        sf = selfRecorderForm()
        ff = formatForm()
        
        valid &= rf.validates()
        for p in pfs:
            p.validates()
        valid &= ef.validates() 
        valid &= sf.validates() 
        valid &= ff.validates()

        if not valid:
            return render.recorder(rf, pfs, ef, sf, ff, self.title)
        #Запись парметров
        xml['id'] = rf.id.value
        xml['station_name'] = rf.stationName.value
        xml['name'] = rf.name.value
        
        for i in xrange(len(pfs)):
            inUse = 'yes'
            if not getattr(pfs[i], 'pov%s' % i).get_value():
                inUse = 'no'
            xml['device'][str(i)]['in_use'] = inUse

            a, d = '0', '128'
            print getattr(pfs[i], 'signals%s' % i).value, signals[0]
            if getattr(pfs[i], 'signals%s' % i).value == signals[0]:
                a, d = '16', '32'
            setDevSigNum(str(i), a, d)
        
        xml['emergency']['prehistory_ms'] = ef.prehistoryMs.value
        xml['emergency']['after_history_ms'] = ef.afterHistoryMs.value
        #FIXME ms=>s
        xml['emergency']['max_file_length_ms'] = str(int(ef.maxFileLengthS.value)*1000)
        xml['emergency']['max_storage_time_day'] = ef.maxStorageTimeDay.value

        xml['self-recorder']['live_update_ms'] = sf.liveUpdateMs.value
        xml['self-recorder']['analog_delta_percent'] = sf.analogDeltaPercent.value
        xml['self-recorder']['max_file_length_hour'] = sf.maxFileLengthHour.value
        xml['self-recorder']['max_storage_time_day'] = sf.maxSelfRecStorageTimeDay.value

        xml['data_formats']['comtrade']['codeset'] = ff.codeset.value
        f = 'BIN'
        if ff.format.value == comtradeFormats[0]:
            f = 'ASCII'
        xml['data_formats']['comtrade']['data_file'] = f
        print xmlRender(xml)
        return render.completion(self.title, 'Данные записаны')

    def GET(self):
        web.header('Content-Type', 'text/html; charset= utf-8')
        
        rf = recorderForm()
        rf.id.value = xml['id']
        rf.stationName.value = xml['station_name']
        rf.name.value = xml['name']
        pfs = povForms
        for i in xrange(len(pfs)):
            getattr(pfs[i], 'pov%s' % i).set_value(xml['device'][str(i)]['in_use'] == "yes")
            si = 0
            if xml['device'][str(i)]['discretes'] == '128': 
                si = 1
            getattr(pfs[i], 'signals%s' % i).value = signals[si]
        ef = emergencyForm()
        ef.prehistoryMs.value = xml['emergency']['prehistory_ms']
        ef.afterHistoryMs.value = xml['emergency']['after_history_ms']
        #FIXME ms=>s
        ef.maxFileLengthS.value = str(int(xml['emergency']['max_file_length_ms'])/1000)
        ef.maxStorageTimeDay.value = xml['emergency']['max_storage_time_day']

        sf = selfRecorderForm()
        sr = xml['self-recorder']
        sf.liveUpdateMs.value = sr['live_update_ms']
        sf.analogDeltaPercent.value = sr['analog_delta_percent']
        sf.maxFileLengthHour.value = sr['max_file_length_hour']
        sf.maxSelfRecStorageTimeDay.value = sr['max_storage_time_day']
        
        ff = formatForm()
        if xml['data_formats']['choice'] == 'comtrade':
            ff.codeset.value = xml['data_formats']['comtrade']['codeset']
            fi = 0
            if xml['data_formats']['comtrade']['data_file'] == 'BIN': 
                fi = 1
            ff.format.value = comtradeFormats[fi]

        return render.recorder(rf, pfs, ef, sf, ff, self.title)


if __name__ == '__main__':
    pass
