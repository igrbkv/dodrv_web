# -*- coding: utf-8 -*-
"""
Отображение текущих значений дискретных сигналов.
Формат:
Текущие значения дискрет 
ПОВ [1]  2  3  4    - присутствует, если больше одного устройства
номер| имя сигнала | значение 
...
"""
import web
from web import form
from config import render, xml, xmlRender, rewriteConfigXml
from utils import readShmem
from formatting import getFirstDev

title = 'Текущие значения дискрет'

class DState:

    def GET(self, dev=''):
        """
        Преобразует данные из разделяемой памяти к списку вида:
        [[<d0_name>, <d0_value>], [<d1_name>, <d1_value>],...}
        @param dev номер устройства
        @return текущ_номер_устройства, дискреты, титул
        """
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')
        
        if not dev:
            dev = getFirstDev()
            if not dev:
                return render.emptypage(title = title)

        discretes = []
        curData = readShmem(dev)
        if curData:
            discretes = [['', ''] for i in xrange(int(xml['device'][dev]["discretes"]))]
            for l in curData:
                if l[0] == 'D':
                    d = xml['device'][dev]['discrete'][l[1]]
                    discretes[int(l[1])][0] = d['alias']
                    if d['in_use'] == 'yes':
                        discretes[int(l[1])][1] = l[2]

        return render.dstate(dev, discretes, title = title)

