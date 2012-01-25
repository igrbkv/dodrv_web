# -*- coding: utf-8 -*-
"""
Отображение текущих значений аналоговых сигналов.
Формат:
Окно 1
Текущие значения аналогов 
ПОВ [1]  2  3  4    - присутствует, если больше одного устройства
номер | имя сигнала | ДЗ 2 | Д3 1 | Угол |искрографик
...

Данные с АЦП(ссылка)  

ДЗ 2 - ДЗ во вторичной/измерительной обмотке трансформатора

Окно 2
Данные с АЦП
ПОВ [1]  2  3  4    - присутствует, если больше одного устройства
номер | имя сигнала |        Значения
      |             |  |  |  |  | ...
Текущие значения аналогов (ссылка)
"""

import web
from config import render, xml
from utils import readShmem, toSI, spark_string
from math import sqrt, pi
from numpy import fft, angle
from http import nocache
from formatting import getFirstDev

ADCCOEF = 10./((1<<13)/2)

class AState:
    skews = []
    title = 'Текущие значения аналогов'
    
    def _calcSkews(self, dev):
        '''
        FIXME вынести расчет в загрузку модуля
        Вычисляет сдвиги фаз, записывает в список вида:
        [(в_радианах, в_град),...]

        '''
        if xml['device'][dev]['skew'] == 'yes':
            rate = int(xml['device'][dev]['sample_rate'])
            self.skews = [(2*pi*50/rate/16*i, 360.*50/rate/16*i) for i in xrange(16)]
            self.skews.insert(0, self.skews.pop())
        else:
            self.skews = [(0,0),]*16

    def _calcRMS(self, coef1, coef2, values, sinusoid):
        if sinusoid:
            rms2 = ADCCOEF*coef2*sqrt(sum([v*v for v in values])/len(values))
        else:
            rms2 = ADCCOEF*coef2*(sum(values)/len(values))
        rms1 = coef1*rms2
        return rms1, rms2
    
    def _angle(self, values, idx, deg=1):
        '''
        Значения на периоде => 
        вектора (в комлЕксном виде) =>
        угол фазы = угол певого вектора
        '''
        ang = angle(fft.fft(values), deg)[1]
        print ang
        ang -= self.skews[idx][deg]
        if ang < 0.:
            ang += 360. if deg else 2.*pi 
        return ang


    def GET(self, dev=''):
        """
        Преобразует данные из разделяемой памяти
        A,<analog_id>,<value1>,<value2>...
        ...
        к списку:
        [<analog_id>,<analog_name>,<дз1>,<дз2>,<угол>,<график>]
        """

        nocache()

        if not dev:
            dev = getFirstDev()
            if not dev:
                return render.emptypage(title = self.title)

        self._calcSkews(dev)
        curData = readShmem(dev)

        data = [[] for i in xrange(int(xml['device'][dev]['analogs']))]
        for l in curData:
            try:
                if l[0] is 'A':
                    lst = []
                    a = xml['device'][dev]['analog'][l[1]]
                    values = [int(v) for v in l[2:]]
                    # <id>
                    lst.append(l[1])

                    # <name>
                    lst.append(a['alias'])

                    unit = xml['ADCs'][a['ADC']]['unit'].encode('utf-8')
                    coef1 = float(a['coef1'])
                    coef2 = float(xml['ADCs'][a['ADC']]['coef2'])
                    sinusoid = a['sinusoid'] == 'yes'
                    rms1, rms2 = self._calcRMS(coef1, coef2, values, sinusoid)
                    # <rms1>
                    lst.append(toSI(str(rms1)) + unit)
                    # <rms2>
                    lst.append(toSI(str(rms2)) + unit)

                    # <angle>
                    ang = '' if not sinusoid else "%.1f" % self._angle(values, int(l[1]))
                    lst.append(ang)

                    # <grafic>
                    minVal = min(values)
                    normValues = [i-minVal for i in values]
                    lst.append(spark_string(normValues))

                    data[int(l[1])] = lst

            except:
                pass

        return render.astate(dev, data, title = self.title)

class ACDState:
    title = 'Данные с АЦП'
    def GET(self, dev=''):
        """
        Преобразует данные из разделяемой памяти
        A,<analog_id>,<value1>,<value2>...
        ...
        к списку:
        [[<id1>, <id2>,...>
        [<value1_1>,<value2_1>,...]
         [<value1_2>,<value2_2>...]
        ...
        [...]]
        """

        nocache()

        if not dev:
            dev = getFirstDev()
            if not dev:
                return render.emptypage(title = self.title)
 
        curData = readShmem(dev)

        data = []
        dataRoll = []
        for l in curData:
            #try
            if l[0] is 'A':
                l.pop(0)
                data.append(l)
        if data:
            w = len(data)
            h = len(data[0])
            dataRoll = [[] for i in xrange(h)]
            for i in xrange(w):
                for j in xrange(h):
                    dataRoll[j].append(data[i][j])

        return render.acdstate(dev, dataRoll, title = self.title)
