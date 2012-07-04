# -*- coding: utf-8 -*-
"""
Отображение состояния сети.
1. Используется команда ifconfig
eth0      Link encap:Ethernet  HWaddr 00:26:9e:4f:b5:9d  
          UP BROADCAST MULTICAST  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)
          Interrupt:22 

lo        Link encap:Local Loopback  
          inet addr:127.0.0.1  Mask:255.0.0.0
          inet6 addr: ::1/128 Scope:Host
          UP LOOPBACK RUNNING  MTU:16436  Metric:1
          RX packets:55 errors:0 dropped:0 overruns:0 frame:0
          TX packets:55 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0 
          RX bytes:13419 (13.1 KiB)  TX bytes:13419 (13.1 KiB)

ppp0      Link encap:Point-to-Point Protocol  
          inet addr:90.143.160.177  P-t-P:10.64.64.64  Mask:255.255.255.255
          UP POINTOPOINT RUNNING NOARP MULTICAST  MTU:1500  Metric:1
          RX packets:4 errors:0 dropped:0 overruns:0 frame:0
          TX packets:5 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:3 
          RX bytes:52 (52.0 B)  TX bytes:80 (80.0 B)

wlan0     Link encap:Ethernet  HWaddr 0c:60:76:67:70:92  
          inet addr:192.168.1.35  Bcast:192.168.1.255  Mask:255.255.255.0
          inet6 addr: fe80::e60:76ff:fe67:7092/64 Scope:Link
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:1630 errors:0 dropped:0 overruns:0 frame:0
          TX packets:4457 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:209167 (204.2 KiB)  TX bytes:458562 (447.8 KiB)

2. Формат страницы:
Состояние сети

Локальная сеть (Ethernet)
Интерфейс:eth0 МАС:0c:60:76:67:70:92
Адрес:192.168.1.35 Маска: 255.255.255.0
Принято пакетов:1630 (209167 байт) Ошибок: 0
Передано пакетов:4457 (458562 байт) Ошибок: 0

Модем (Point-to-Point Protocol)
Интерфейс:ppp0
Адрес:90.143.160.177 Адрес абонента:10.64.64.64
Принято пакетов:4 (52 байт) Ошибок: 0
Передано пакетов:5 (80 байт) Ошибок: 0
"""
import web
from config import render
from subprocess import Popen, PIPE

title = 'Состояние сети'

def parval(pars, par):
    '''
    return <val> from [..., <par>:<val>,...]
    '''
    for w in pars:
        if w.startswith(par+':'):
            return w.split(':')[1]
    return ''


def ifconfig():
    '''
    Разбор в словарь словарей:
    {
    'eth0':{
        'Link':'Ethernet', 'HWaddr':'0c:60:76:67:70:92',
        'addr':'192.168.1.35', 'P-t-P':'',
        'Mask':'255.255.255.0', 
        'RX_packets':'1630', 
        'RX_errors':'0', 'RX_dropped':'0', 'RX_overruns':'0', 'RX_frame':'0',
        'TX_packets':'4457'
        'TX_errors':'0', 'TX_dropped':'0', 'TX_overruns':'0', 'TX_carrier':'0',
        'RX_bytes':'209167', 'TX_bytes':'458562'
        }
    'ppp0':{
    ...
    }
    }
    '''
    res = {}
    par = ['ifconfig']
    lines = Popen(par, stdout = PIPE).communicate()[0].split('\n')
    ifname = ''
    pars = {}
    state = 'encap'
    for l in lines:
        if not l:
            state = 'encap'
            pars = {}
            continue

        l = l.split()
        val = parval(l, state)
        if not val:
            continue

        if state == 'encap':
            ifname = l[0]
            pars[state] = val 
            state = 'HWaddr'
            pars[state] = l[l.index(state)+1] if state in l else ''
            state = 'addr'
        elif state == 'addr':
            pars[state] = val
            state = 'P-t-P'
            pars[state] = parval(l, state)
            state = 'Mask'
            pars[state] = parval(l, state)
            state = 'MTU'
        elif state == 'MTU':
            state = 'RUNNING'
            if state in l:
                state = 'frame'
        elif state == 'frame':
            prefix = 'RX_'
            pars[prefix+state] = val
            state = 'packets'
            pars[prefix+state] = parval(l, state)
            state = 'errors'
            pars[prefix+state] = parval(l, state)
            state = 'dropped'
            pars[prefix+state] = parval(l, state)
            state = 'overruns'
            pars[prefix+state] = parval(l, state)
            state = 'carrier'
        elif state == 'carrier':
            prefix = 'TX_'
            pars[prefix+state] = val
            state = 'packets'
            pars[prefix+state] = parval(l, state)
            state = 'errors'
            pars[prefix+state] = parval(l, state)
            state = 'dropped'
            pars[prefix+state] = parval(l, state)
            state = 'overruns'
            pars[prefix+state] = parval(l, state)
            state = 'bytes'
        elif state == 'bytes':
            prefix = 'RX_'
            pars[prefix+state] = val
            prefix = 'TX_'
            pars[prefix+state] = parval(l[l.index('TX'):], state)
            
            res[ifname] = pars
    
    return res

class NetState:
    def GET(self):
        """
        """
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')

        ifl = []
        ifd = ifconfig()

        # Преобразование в список списков с форматированием
        # [[<имя1>,[<параметры_строка1>, <параметры_строка2>, ...]], [[...,[...]]]...]
        for k, v in ifd.iteritems():
            l = []
            if v['encap'] == 'Point-to-Point':
                l.append('Модем (%s)' % v['encap'])
            elif v['encap'] == 'Ethernet':
                l.append('Локальная сеть (%s)' % v['encap'])
            else:
                continue
            
            ll = []
            if v['HWaddr']:
                ll.append('Интерфейс:%s MAC:%s' % (k, v['HWaddr']))
            else:
                ll.append('Интерфейс:%s' % k)

            if v['P-t-P']:
                ll.append('Адрес:%s Адрес абонента:%s' % (v['addr'], v['P-t-P']))
            else:
                ll.append('Адрес:%s Маска сети:%s' % (v['addr'], v['Mask']))

            ll.append('Принято пакетов:%s (%s байт) Ошибок:%s Потеряно:%s' %\
                (v['RX_packets'], v['RX_bytes'], v['RX_errors'], v['RX_dropped']))
            ll.append('Передано пакетов:%s (%s байт) Ошибок:%s Потеряно:%s' %\
                (v['TX_packets'], v['TX_bytes'], v['TX_errors'], v['TX_dropped']))
            l.append(ll)
            ifl.append(l)


        return render.netstate(ifl, title = title)
