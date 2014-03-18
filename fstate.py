# -*- coding: utf-8 -*-
"""
Отображение текущих значений фильтров аналоговых сигналов.
Формат:
Текущие значения фильтров
ПОВ [1]  2  3  4    - присутствует, если больше одного устройства
имя сигнала | нижняя граница | текущее значение* | верхняя граница
ДЗ
...
ПП
...
ОП
...
НП
...
P
...
Q
...
H

* - текущее значение отображается синим, если меньше НГ, красным, если больше ВГи зеленым в противном случае
"""
import web
from config import render, xml
from utils import readShmem, toSI
from formatting import getFirstDev


title = 'Текущие значения фильтров'

fltNames = {'RMS':('rms', '', 'Действующее значение'), \
        'PPS': ('positive_phase_sequence', '', 'Прямая последовательность'), \
        'NPS': ('negative_phase_sequence', '', 'Обратная последовательность'), \
        'ZPS': ('zero_phase_sequence', '', 'Нулевая последовательность'), \
        'H': ('harmonic', '', 'Гармоника'), \
        'P': ('active_power', 'Вт', 'Активная мощность'), \
        'Q': ('reactive_power', 'Вар', 'Реактивная мощность')}


class FState:
    def _sigName(self, dev, num):
        """
        @return имя сигнала, а если его нет, то A:<num>
        """
        n = xml['device'][dev]['analog'][num]['alias']
        if not n:
            n = u'A:' + num
        return n

    def GET(self, dev=''):
        """
        Преобразует данные из разделяемой памяти
        <filter_name>,<analog_id>,<value>
        ...
        к словарю:
        filters={'Действующее значение':[(<analog_id>|<analog_name>),<bottom_threshold>,<value_lst>,<top_threshold>],...]}
        где <value_lst> = [<value_if_lt_bottom>,<value>,<value_if_gt_top>]

        @param dev номер устройства
        @return текущ_номер_устройства, filters, титул
        """
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')

        if not dev:
            dev = getFirstDev()
            if not dev:
                return render.emptypage(title = title)

        filters = dict([(n[2], []) for n in fltNames.values()])

        curData = readShmem(dev)
        for l in curData:
            try:
                if l[0] in fltNames.keys():
                    lst = []
                    fltXmlName = fltNames[l[0]][0]
                    a = xml['device'][dev]['analog'][l[1]]

                    # <имя>
                    n = self._sigName(dev,l[1])
                    # для последовательностей добавляются фазы B,C
                    if l[0] in ('PPS', 'NPS', 'ZPS'):
                        n += ', ' + self._sigName(dev, a[fltXmlName]['id_b']) + \
                            ', ' + self._sigName(dev, a[fltXmlName]['id_c'])
                    lst.append(n)
                    unit = fltNames[l[0]][1]
                    if not unit:
                        unit = xml['ADCs'][a['ADC']]['unit'].encode('utf-8')
                    bottom = a[fltXmlName]['analog_emergency']['bottom_threshold']
                    top = a[fltXmlName]['analog_emergency']['top_threshold']
                    value = toSI(l[2]) + unit

                    # <bottom_threshold>
                    if bottom:
                        lst.append(toSI(bottom)+unit)
                    else:
                        lst.append('')

                    # <value_lst>
                    vl=[ '', '', '']
                    if bottom and float(l[2] < float(bottom)):
                        vl[0] = value
                    elif top  and float(l[2]) > float(top):
                        vl[2] = value
                    else:
                        vl[1] = value
                    lst.append(vl)

                    # <top_threshold>
                    if top:
                        lst.append(toSI(top)+unit)
                    else:
                        lst.append('')

                    filters[fltNames[l[0]][2]].append(lst)

            except:
                #FIXME Сообщение об ошибке в syslog
                pass


        return render.fstate(dev, filters, title = title)
