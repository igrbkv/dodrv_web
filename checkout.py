# -*- coding: utf-8 -*-

'''
Поверка регистратора.
Экраны:
1.
Поверка
Первичная поверка   [v]
ПУ 0                [v]
ПУ 1                [v]
ПУ 2                [v]
ПУ 3                [v]

[Начать]

Результаты поверки
Дата
01/01/2014 00:00:00     [Удалить]
...
2.
Поверка
Номер сигнала   А 0:0
Имя             Фаза А
Датчик          ТТ-8

Подайте 35А

[Выполнено] [Пропустить]
3.


************************************
В начале поверки создается файл со всеми проверяемыми сигналами
/tmp/recorder_checkout,
<Первичная поверка f|p>,<ПОВ0 0|1>, ..., <ПОВ5 0|1>
<Проверен 0|1|<пробел-пропуск>>,<ПОВ N>,<N сигнала>
    <~|-|0 - переменный ток(alternating current)|постоянный(direct current)|проверка нуля>,
    <коэффициент>,<номинальное значение>,<допускаемая погрешность>,
    <измеренное значение>,<погрешность измерения>
.
который по окончании переписывается в
/etc/dodrv/checkout_reports/140101000000[f|p].chk
Формат файла:
<Первичная поверка f|p>,<ПОВ0 0|1>, ..., <ПОВ5 0|1>
<Проверен 0|1|<пробел-пропуск>>,<ПОВ N>,<N сигнала>,<имя сигнала>,
    <имя датчика>,<coef2><V|A>,<предел переменного тока>,
    <предел постоянного тока>,<~|-|0 - переменный ток|постоянный|проверка нуля>,
    <коэффициент>,<номинальное значение>,<допускаемая погрешность>,
    <измеренное значение>,<погрешность измерения>
...
'''
import web
from web import form
from config import render, xml, DEBUG_PATH, MAX_POV
from formatting import getFirstDev
from http import nocache
from os import listdir, path, stat, remove, makedirs
from datetime import datetime
from utils import toSI
from math import sqrt
if not DEBUG_PATH:
    from utils import readShmem, recorderMode

ADCCOEF = 10./((1<<13)/2)
SQRT2 = 1.4142135623730951
CHECKOUT_REPORTS_PATH = DEBUG_PATH + '/var/db/checkout_reports'
CUR_CHECKOUT_PATH = DEBUG_PATH + '/tmp/recorder_checkout'

firstCheckout = form.Form(form.Checkbox('first_checkout', value = 'value',
    checked = True, description = 'Первичная поверка'))

if DEBUG_PATH:
    def readShmem(dev):
        '''
        <name>,N,<value1>...
        =>
        [[<name>,N,<value1>,...], ...]
        '''
        lines = []
        with open(DEBUG_PATH + "/dev/shm/pov" + dev, 'r') as shm:
            for l in shm:
               lines.append(l.split(','))
        return lines

    def recorderMode(value=''):
        return 0


def createPovs(ca):
    pf = []
    for i in xrange(MAX_POV):
        if xml['device'].has_key(str(i)) and xml['device'][str(i)]['exists']\
            and xml['device'][str(i)]['in_use'] == "yes":
            p = form.Checkbox('pov%d' % i, value = '%d' % i, 
                checked = bool(int(ca[i])), description = 'Канал %d' % i)
            pf.append(p)
    return pf


buttonBegin = form.Button('form_action', value = 'begin', html = u'Начать')
buttonContinue = form.Button('form_action', value = 'continue', html = u'Продолжить')
buttonFinish = form.Button('form_action', value = 'finish', html = u'Закончить')

def createReports():
    rf = []
    reports = []
    try:
        reports = sorted(listdir(CHECKOUT_REPORTS_PATH))
    except:
        pass
    for i in xrange(len(reports)):
        b = form.Button('form_action', value = reports[i],
            html = u'Удалить')
        rf.append(b)
    return rf

def checkSignal(fc, a):
    sl = []
    diapasons=((0.1, 0.3, 0.5, 0.75, 1.), (0.1, 0.3, 0.5, 0.75, 1.), (0.0,))
    adc = xml['ADCs'][a['ADC']]
    adc['name'] = a['ADC']
    pat = '0,%s,%s' % (a['pov'], a['id'])
    types = ('~', '+', '+')
    limits = (float(adc['checkout_AC']), float(adc['checkout_DC']),
        float(adc['checkout_Z']))
    fcc = 0.8 if fc else 1.0
    percent = float(adc['checkout_PE'])
    unitA = adc['unit'] == 'A'
    for d in xrange(len(diapasons)):
        l = '%s,%s' % (pat, types[d])
        for dd in xrange(len(diapasons[d])):
            if d == 2:
                ll = '%s,%.2f,0,%f,,,\n' % (l, diapasons[d][dd],
                    limits[d]*percent*fcc/100.)
            else:
                v = limits[d]
                # упрощенная поверка
                if v == 0.:
                    break
                perc = percent
                if perc == 0.5:
                    perc += 0.05*(1./diapasons[d][dd]-1.)
                ll = '%s,%.2f,%f,%.2f,,,\n' % (l, diapasons[d][dd],
                    v*diapasons[d][dd], perc*fcc)
            sl.append(ll)
    return sl


def createCheckoutFile(fc, povs):
    with open(CUR_CHECKOUT_PATH, 'w') as cf:
        cf.write('f' if fc else 'p')
        for p in povs:
            cf.write(',1' if p else ',0')
        cf.write('\n')
        for i in xrange(MAX_POV):
            if povs[i]:
                for j in xrange(int(xml['device'][str(i)]['analogs'])):
                    a = xml['device'][str(i)]['analog'][str(j)]
                    if a['in_use'] == 'yes':
                        a['pov'] = str(i)
                        cf.writelines(checkSignal(fc, a))

def finishCheckout():
    fname = ''
    if path.isfile(CUR_CHECKOUT_PATH):
        with open(CUR_CHECKOUT_PATH, 'r') as cf:
            flag = cf.readline()[0]
            ts = datetime.fromtimestamp(stat(CUR_CHECKOUT_PATH)[7])
            lines = cf.readlines()
        remove(CUR_CHECKOUT_PATH)
        fname = '%02d%02d%02d%02d%02d%02d_%s.chk'% (ts.year%100, ts.month,
            ts.day, ts.hour, ts.minute, ts.second, flag)

        with open('%s/%s' % (CHECKOUT_REPORTS_PATH, fname), 'w') as cf:
            cf.write('<table>\n')
            cf.write('<tr><td>Регистратор электрических процессов цифровой %s.</td></tr>\n' %
                xml['type'].encode('utf-8'))
            cf.write('<tr><td>Протокол %s поверки.</td></tr>\n' % ('первичной' if flag == 'f' else 'периодической'))
            cf.write('<tr><td>Дата: %02d.%02d.%d %02d:%02d</td></tr>\n' % (ts.day, ts.month, ts.year, ts.hour, ts.minute))
            cf.write('<tr><td>Энергообъект: %s</td></tr>\n' % (xml['station_name'].encode('utf-8')))
            cf.write('<tr><td>Установочный номер: %s</td></tr>\n' % (xml['id'].encode('utf-8')))
            cf.write('</table>\n')

            pu = ''
            sid = ''
            unit = ''
            for l in lines:
                l = l.strip().split(',')
                if l[0] == '1':
                    if l[1] != pu or  l[2] != sid:
                        if pu:
                            cf.write('</table>\n')
                        pu = l[1]
                        sid = l[2]
                        a = xml['device'][pu]['analog'][sid]
                        adc = xml['ADCs'][a['ADC']]
                        unit = adc['unit']
                        cf.write('<p><table>\n')
                        cf.write('<tr><td>ПУ: %s</td></tr>\n' % pu)
                        cf.write('<tr><td>Сигнал: %s(%s)</td></tr>\n' % (sid, a['alias'].encode('utf-8')))
                        cf.write('<tr><td>Модуль: %s(%s)</td></tr>\n' % (adc['name'].encode('utf-8'), adc['coef2'].encode('utf-8')))
                        cf.write('<tr><td>Предел модуля: %s %s</td></tr>\n' % (frmtAdc(adc).encode('utf-8'), adc['unit'].encode('utf-8')))
                        cf.write('</table></p>\n')
                        cf.write('<table>\n')
                        cf.write('<tr><th>Коэффициент</th><th>Номинальное значение</th><th>Измеренное значение</th><th>Погрешность измерения</th><th>Допускаемая погрешность измерения</th><th></th></tr>\n')
                    cf.write('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' % frmtLine(l, unit))

            if pu:
                cf.write('</table>\n')
    return fname

def frmtAdc(adc):
    ac = ''
    sep = ''
    dc = ''
    if float(adc['checkout_AC']) != 0.:
        ac = '~%s' % adc['checkout_AC']
    if float(adc['checkout_DC']) != 0.:
        sep = '/'
        dc = '+%s' % adc['checkout_DC']

    return '%s%s%s' % (ac, sep, dc)

def frmtLine(line, unit):
    '''
    0 1 2 3   4     5      6          7         8      9
    1,0,0,+,0.30,0.060000,2.40    ,0.0598765,2.398765 , ; V
    1,0,0,+,0.00,0       ,0.004800,0.0054321,0.0054321,*; V
    =>
     коэф     номинал   измерен  погр.изм. д.погр  флаг ош.
    ('0.30', '+60mV', '+59.87mV', '2.39%',  '2.40%' , '' )
    ('0.00', '+0V'  , '+5.432mkV','5.43mkV','4.8mkV', '*' )

    '''
    nominal = '%s%s%s' % (line[3], toSI(line[5]), unit)
    v = float(line[7])
    if v >= 0.:
        val = '%s%s%s' % (line[3], toSI(line[7]), unit)
    else:
        val = '%s%s' % (toSI(line[7]), unit)
    v = float(line[8])
    if line[5] == '0':
        limit = '%s%s' % (toSI(line[6]), unit)
        res = val
    else:
        limit = '%s%%' % line[6]
        res = '%.3f%%' % v
    return (line[4], nominal, val, res, limit, line[9])

def currentSignal():
    with open(CUR_CHECKOUT_PATH, 'r') as ccp:
        for s in ccp:
            if len(s) and s[0] == '0':
                sig = s.strip().split(',')
                a = xml['device'][sig[1]]['analog'][sig[2]]
                adc = xml['ADCs'][a['ADC']]
                return (sig[1], '%s(%s)' % (sig[2], a['alias']), 
                    '%s %s %s' % (adc['name'], frmtAdc(adc), adc['unit']),
                    '%s%s%s' % (sig[3],toSI(sig[5]), adc['unit']))
    return None

title = 'Поверка'

class Checkout:

    def GET(self):
        nocache()
        ca = []

        if not path.isdir(CHECKOUT_REPORTS_PATH):
            makedirs(CHECKOUT_REPORTS_PATH)

        fc = firstCheckout
        fileExists = path.isfile(CUR_CHECKOUT_PATH)
        if fileExists:
            with open(CUR_CHECKOUT_PATH, 'r') as ccp:
                pars = ccp.readline().strip().split(',')
                if pars[0] == 'p':
                    fc['first_checkout'].set_value(False)
                ca = pars[1:]
        else:
            ca = [True for i in xrange(MAX_POV)]
        povs = createPovs(ca)
        reports = createReports()

        return render.checkout(fileExists,
            fc, povs,
            buttonBegin, buttonContinue, buttonFinish,
            reports, title = title)

    def POST(self):
        nocache()
        self.i = web.input()
        if self.i.form_action == 'begin':
            fc = firstCheckout
            fc.validates()
            povs = [False for i in xrange(MAX_POV)]
            for i in xrange(MAX_POV):
                p='pov%d' % i
                if p in self.i:
                    povs[i] = True
            createCheckoutFile(fc['first_checkout'].get_value(), povs)
            recorderMode(value=1)
            return web.seeother('/config/checkadc')
        elif self.i.form_action == 'finish':
            report = finishCheckout()
            recorderMode(value=0)
            return web.seeother('/config/report/%s' % report)
        elif self.i.form_action == 'continue':
            return web.seeother('/config/checkadc')
        else:
            remove('%s/%s' % (CHECKOUT_REPORTS_PATH, self.i.form_action))

        return self.GET()

class Report:
    def GET(self, report):
        nocache()
        with open('%s/%s' % (CHECKOUT_REPORTS_PATH, report), 'r') as rf:
            lines = rf.readlines()
        return render.checkout_report(lines, title = title)

class Adc:
    def __init__(self):
        self.title = title
        fileExists = path.isfile(CUR_CHECKOUT_PATH)
        if fileExists:
            with open(CUR_CHECKOUT_PATH, 'r') as ccp:
                if ccp.readline()[0] == 'p':
                    self.title = 'Периодическая поверка'
                else:
                    self.title = 'Первичная поверка'

    def GET(self, note = ''):
        nocache()

        sig = currentSignal()
        if not sig:
            report = finishCheckout()
            recorderMode(value=0)
            #return web.seeother('/config/checkout')
            return web.seeother('/config/report/%s' % report)
        return render.checkadc(note, sig, title = self.title)

    def _calcRMS(self, coef2, values, sinusoid):
        if sinusoid:
            rms2 = ADCCOEF*coef2*sqrt(sum([v*v for v in values])/len(values))
        else:
            rms2 = ADCCOEF*coef2*(sum(values)/len(values))
        return rms2

    def POST(self):
        nocache()

        self.i = web.input()
        note = ''
        lines = []

        with open(CUR_CHECKOUT_PATH, 'r') as ccp:
            lines = ccp.readlines()
        for i in xrange(len(lines)):
            if len(lines[i]) and lines[i][0] == '0':
                sig = lines[i].split(',')
                a = xml['device'][sig[1]]['analog'][sig[2]]
                adc = xml['ADCs'][a['ADC']]

                if self.i.form_action == 'skip':
                    lines[i] = ' %s' % lines[i][1:]
                elif self.i.form_action == 'ready':
                    curData = readShmem(sig[1])
                    if not curData:
                        note = 'Нет данных'
                        break

                    vals = []
                    for l in curData:
                        if l[0] == 'A' and l[1] == sig[2]:
                            vals = [int(v) for v in l[2:]]
                            break
                    if not l:
                        note = 'Нет данных'
                        break

                    # FIXME перегрузка
                    for j in xrange(len(vals)-1):
                        if abs(vals[j]) >= 2047 and vals[j] == vals[j+1]:
                            note = 'Перегрузка'
                            break
                    if note: break

                    val = self._calcRMS(float(adc['coef2']), vals, sig[3] == '~')
                    sig[7] = str(val)
                    # погрешность
                    if sig[3] != '0':
                        # приведенная (val-nominal)/max*100
                        val=(val-float(sig[5]))/(ADCCOEF*2048.0*float(adc['coef2']))*100
                        # FIXME В досовской версии max умножался на SQRT2 даже
                        # для постоянного тока, хотя по идее должен делиться
                        # и то только для переменного:
                        # (val-nominal)/(max/SQRT2)*100
                        if sig[3] == '~':
                            val *= SQRT2

                    #else:
                        # абсолютная

                    sig[8]=str(val)
                    if abs(val) > float(sig[6]):
                        sig[9] = '*\n'
                    sig[0] = '1'
                    lines[i] = ','.join(sig)
                break

        if not note:
            with open(CUR_CHECKOUT_PATH, 'w') as cf:
                cf.writelines(lines)

        return self.GET(note=note)
