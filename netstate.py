# -*- coding: utf-8 -*-
"""
Отображение состояния сети.
1. Используется команда ifconfig
eth0: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500
        ether 00:26:9e:4f:b5:9d  txqueuelen 1000  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 0  (Local Loopback)
        RX packets 30  bytes 3724 (3.6 KiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 30  bytes 3724 (3.6 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

ppp0: flags=4305<UP,POINTOPOINT,RUNNING,NOARP,MULTICAST>  mtu 1500
        inet 90.138.152.107  netmask 255.255.255.255  destination 10.64.64.64
        ppp  txqueuelen 3  (Point-to-Point Protocol)
        RX packets 4  bytes 52 (52.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 5  bytes 80 (80.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.35  netmask 255.255.255.0  broadcast 192.168.1.255
        inet6 fe80::e60:76ff:fe67:7092  prefixlen 64  scopeid 0x20<link>
        ether 0c:60:76:67:70:92  txqueuelen 1000  (Ethernet)
        RX packets 3405  bytes 1942730 (1.8 MiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 2388  bytes 234444 (228.9 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

2. Формат страницы:
Состояние сети

Локальная сеть (Ethernet)
Интерфейс:eth0 
Адрес:192.168.1.35 Маска: 255.255.255.0
МАС:0c:60:76:67:70:92
Принято пакетов:1630 (209167 байт) 
Ошибок приема: 0
Передано пакетов:4457 (458562 байт) 
Ошибок передачи: 0

Модем (Point-to-Point Protocol)
Интерфейс:ppp0
Адрес:90.143.160.177 Адрес абонента:10.64.64.64
Принято пакетов:4 (52 байт) 
Ошибок приема: 0
Передано пакетов:5 (80 байт) 
Ошибок передачи: 0
"""
import web
from config import render
from subprocess import Popen, PIPE

title = 'Состояние сети'

def ifconfig():
   
    return res

class NetState:
    def GET(self):
        """
        """
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')

        res = []
        par = ['ifconfig']
        lines = Popen(par, stdout = PIPE).communicate()[0].split('\n')
        ifname = ''
        for l in lines:
            if not l:
                ifname = ''
                continue

            if ifname == '':
                l = l.split(':')
                ifname = l[0]
                if 'eth' in ifname:
                    res.append(u'')
                    res.append(u'Локальная сеть (Ethernet)')
                    res.append(u'Интерфейс:' + ifname)
                elif 'ppp' in ifname:
                    res.append(u'')
                    res.append(u'Модем (Point-to-Point Protocol)')
                    res.append(u'Интерфейс:' + ifname)
                else:
                    ifname = 'skip'
            elif ifname == 'skip':
                continue
            else:
                l = l.split()
                if l[0] == 'inet':
                    if 'eth' in ifname:
                        res.append(u'Адрес:' + l[1] + u' Маска:' + l[3])
                    else:
                        res.append(u'Адрес:' + l[1] + u' Адрес абонента:' + l[5])
                elif l[0] == 'ether':
                    res.append(u'MAC:' + l[1])
                elif l[0] == 'RX':
                    if l[1] == 'packets':
                        res.append(u'Принято пакетов:' + l[2] + u' байт:' + 
                            l[4] + ' ' + l[5] + ' ' + l[6])
                    elif l[1] == 'errors':
                        res.append(u'Ошибок приема:' + l[2])
                elif l[0] == 'TX':
                    if l[1] == 'packets':
                        res.append(u'Передано пакетов:' + l[2] + u' байт:' + 
                            l[4] + ' ' + l[5] + ' ' + l[6])
                    elif l[1] == 'errors':
                        res.append(u'Ошибок передачи:' + l[2])
        return render.netstate(res, title = title)
