# -*- coding: utf-8 -*-
'''
Форма:
Настройка сетевого интерфейса.
    IP адрес
    Маска сети
    Шлюз

Настройка модема и протокола PPP.
    Порт
    Скорость
    Строка инициализации

    Входящие подключения.
        Отвечать на звонок 
        IP адрес модема
        IP адрес клиента
    
    Исходящие подключения.
        Логин
        Пароль

При входящем подключении регистратору и клиенту всегда
присваиваются заданные адреса. Логин и пароль клиента - те же, что при
подключении к веб-серверу.

При исходящем подключении регистратор всегда использует
один и тот же логин и пароль, а адрес получает от удаленного
сервера.
        
'''
import web
from web import form
from config import render, DEBUG_PATH
from utils import service 
from http import nocache
from configobj import ConfigObj
from IPy import IP
from subprocess import Popen, PIPE, call
import re
from os import rename

DEBUG_PATH = '../doweb/debug'
MGETTY_CONF_PATH = DEBUG_PATH + '/etc/mgetty+sendfax/mgetty.config'


NET_CONFIG_PATH = DEBUG_PATH + '/etc/conf.d/net'
title = 'Настройка сети'
NOTE_INVALID_VALUE = 'Неверное значение'
MAX_RINGS = 8
INITTAB_PATH = DEBUG_PATH + '/etc/inittab'
MGETTY_INITTAB = 'm1:2345:respawn:/sbin/mgetty'
MGETTY_CONF_PATH = '/etc/mgetty+sendfax/mgetty.conf'

ethForm = form.Form(
    form.Textbox('ip_address', 
        form.Validator('Не заполнено', bool),
        description = 'IP адрес'),
    form.Textbox('netmask', 
        form.Validator('Не заполнено', bool),
        description = 'Маска сети'),
    form.Textbox('gateway', description = 'Шлюз'))

modemForm = form.Form(
    form.Dropdown('port', [], description = 'Порт'),
    form.Textbox('init_string', description = 'Строка инициализации'))

inPPPForm = form.Form(    
    form.Dropdown('rings', [(0, 'Нет')] + [(i, str(i)) for i in xrange(1, MAX_RINGS)], description = 'Отвечать на звонок'),
    form.Textbox('modem_ip', description = 'IP адрес модема'),
    form.Textbox('client_ip', description = 'IP адрес клиента'))

outPPPForm = form.Form(
    form.Textbox('recorder_login', description = 'Логин'),
    form.Textbox('recorder_password', description = 'Пароль'))


class Network:
    # значения по умолчанию для mgetty 
    # FIXME не нашел в исходниках debug, хотя в mgetty.conf заявлено, что 4
    mconf = {'port':'', 'speed': '38400', 'init-chat': '', 'debug': 4}

    def __init__(self):
        self.mconf.update(self._readMgettyConf())

    def _getEthParams(self):
        '''
        Читает NET_CONFIG_PATH и возвращает 
        IP-адрес, маску сети и адрес шлюза.
        Проверка не производится, поэтому параметры должны быть следующего 
        вида:
        config_eth0="192.168.0.2 netmask 255.255.255.0"
        routes_eth0="default via 192.168.0.1"

        '''
        config = ConfigObj(NET_CONFIG_PATH)
        config_eth0 = config['config_eth0'].strip().split()
        routes_eth0 = config['routes_eth0'].strip().split()
        return config_eth0[0], config_eth0[2], routes_eth0[2]
    
    def _readMgettyConf(self):
        '''
        mgetty.conf д.б. упрощенной структуры с одной секцией:
        port ttyS<N> #начало секции!!!
        speed PORT_SPEED
        init-chat "" AT<1> OK ... AT<N> OK
        debug 4 #до 9

        return {'name': 'value', ...}

        '''
        d = {}
        section = False
        with open(MGETTY_CONF_PATH) as mc:
            for line in mc:
                line = line.strip()
                if not line or line[0] == '#':
                    continue
                line = line.split()
                if len(line) < 2:
                    continue
                if section:
                    d[line[0]] = ' '.join(line[1:])
                elif line[0] == 'port':
                    section = True
                    d[line[0]] = ' '.join(line[1:])
        return d

    def _writeMgettyConf(self):
        l = []
        if d.has_key('port'):
            # сначала порт
            l.append('port ' + d.pop('port') + '\n')
            for k, v in d.iteritems():
                l.append(k + ' ' + v + '\n')
        with open(MGETTY_CONF_PATH + '.new', 'w') as mc:
            mc.writelines(l)
        rename(MGETTY_CONF_PATH + '.new', MGETTY_CONF_PATH)


    
    def _comPorts(self):
        '''
        Список портов формируется из объединения след. множеств:
        1. устройства, указанного в inittab для запуска mgetty
        2. послед. портов, показанных setserial и занятых/ответивших pppd 
        return <список>, <текущий_порт>
        <текущий_порт> = 0 = порт не задан
        например:
        (1, 4), 1 - (COM1, COM4), где COM1 текущий

        '''
        ports = []
        
        # 1.
        cur_port = 0
        if self.mconf.has_key('port'):
            cur_port = int(self.mconf['port'][-1]) + 1
            ports.append(cur_port)
        with open(INITTAB_PATH) as fp:
            for line in iter(fp.readline, ''):
                if MGETTY_INITTAB[:2] in line[:2]:
                    cur_port = int(line.strip()[-1]) + 1
                    ports.append(cur_port)

        # 2. Проверки слизаны из pppconfig.real
        par = ['setserial', '-g']
        for i in xrange(4):
            par.append('/dev/ttyS%d' % i)
        ttyS = Popen(par, stdout = PIPE).communicate().split('\n')
        busy = not call(['pidof', 'pppd'])
        for t in ttyS:
            if re.search('16[45]50', t):
                tt = re.search('/dev/ttyS[1-4]', t)
                if tt:
                    tt = tt.group()
                    if not busy:
                        pppdRet = Popen(['pppd', 'nodetach', 'noauth', 
                            'nocrtscts', tt, 'connect', 
                            "chat -t1 '' AT OK"], stdout = PIPE).communicate()
                        if 'established' not in pppRet:
                            continue
                    tt = int(tt[-1]) + 1
                    if tt not in par:
                    ports.append(tt)
        
        ports.sort()
        return ports, cur_port


    def GET(self):
        nocache()

        ethFrm = ethForm()
        ethFrm['ip_address'].value,\
        ethFrm['netmask'].value,\
        ethFrm['gateway'].value = self._getEthParams()

        return render.network(ethFrm, title = title)

    def _checkIp(self, ip):
        '''
        Проверка адреса.
        Дополнительно к IP отсекаются короткие адреса
        и адреса с маской (напр.: 127.0, 127.0.0.0/8)
        '''
        if '/' not in ip:
            try:
                IP(ip)
                ip.split('.')[3]
                return True
            except:
                pass
        return False

    def _checkNetmask(self, ip, netmask):
        try:
            IP(ip + '/' + netmask, make_net=True)
        except:
            return False
        return True
    
    def _checkGateway(self, ip, netmask, gateway):
        if gateway:
            ip1 = IP(ip + '/' + netmask, make_net=True)
            ip2 = IP(gateway + '/' + netmask, make_net=True)
            if ip1 != ip2:
                return False
        return True

    def POST(self):
        ethFrm = ethForm()
        valid = ethFrm.validates()
        if valid:
            ip, netmask, gateway = (ethFrm[k].get_value() 
                    for k in ('ip_address', 'netmask', 'gateway'))
            valid = self._checkNetmask(ip, netmask)
            if not valid:
                ethFrm['netmask'].note = NOTE_INVALID_VALUE
            else:
                valid = self._checkGateway(ip, netmask, gateway)
                if not valid:
                    ethFrm['gateway'].note = NOTE_INVALID_VALUE

        if not valid:
            return render.network(ethFrm, title = title)
       
        config = ConfigObj(NET_CONFIG_PATH, list_values = False)
        config['config_eth0'] = '"%s netmask %s"' % (ip, netmask)
        config['routes_eth0'] = '"default via %s"' % gateway
        config.write()

        service('eth0', 'restart')

        return render.completion(title)
