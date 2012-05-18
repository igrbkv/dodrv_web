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
        Логин
        Пароль
        IP адрес клиента
    
    Исходящие подключения.
        Логин
        Пароль

Входящее подключение использует опцию proxyarp, поэтому
модему присваивается адрес сетевого интерфейса (eth0), а клиенту 
заданный адрес, который должен соответствовать локальному сегменту сети.

При исходящем подключении регистратор всегда использует
один и тот же логин и пароль, а адрес получает от удаленного
сервера.

Если модем не задан, остальные параметры могут быть пустыми, иначе
производится проверка как обычно.
'''
from web import form
from config import render, DEBUG_PATH
from utils import service, rewrite 
from http import nocache
from configobj import ConfigObj
from IPy import IP
from subprocess import Popen, PIPE, call
import re

NET_CONFIG_PATH = DEBUG_PATH + '/etc/conf.d/net'
MGETTY_CONF_PATH = DEBUG_PATH + '/etc/mgetty+sendfax/mgetty.config'
INITTAB_PATH = DEBUG_PATH + '/etc/inittab'
PPPD_OPTIONS_PATH = DEBUG_PATH + '/etc/ppp/options'
PPPD_CHAP_SECRETS_PATH = DEBUG_PATH + '/etc/ppp/chap-secrets'
OUTGOUING_CHATSCRIPT_PATH = DEBUG_PATH + '/etc/chatscripts/outgouing'

title = 'Настройка сети'
NOTE_INVALID_VALUE = 'Неверное значение'
MGETTY_INITTAB = 'm1:2345:respawn:/sbin/mgetty'
MGETTY_DEBUG_LVL_MAX = 9
BAUD_RATES = ['2400', '4800', '9600', '19200', '38400', '57600']
REGEXP = '^[0-9a-zA-Z_]*$'
RINGS = [u'Нет'] + [str(i) for i in xrange(1, 8)]
COM_PORTS = [u'Нет', 'COM1', 'COM2', 'COM3', 'COM4']
NOTE_NO_VALUE = 'Значение не задано'

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
    form.Dropdown('speed', BAUD_RATES, description = 'Скорость'),
    form.Textbox('init-chat', description = 'Строка инициализации'),
    form.Checkbox('debug', value = 'value', checked = False, 
        description = 'Протокол'))

inForm = form.Form(    
    form.Dropdown('rings', RINGS, description = 'Отвечать на звонок'),
    form.Textbox('remotename',
        form.Validator('* Длина имени не должна превышать 12 символов', 
            lambda i: len(i) <= 12 ),
        form.regexp(REGEXP, '* Недопустимые символы в имени'),
        description = 'Логин'),
    form.Textbox('remote_password', 
        form.Validator('* Длина пароля не должна превышать 12 символов', 
            lambda i: len(i) <= 12 ),
        form.regexp(REGEXP, '* Недопустимые символы в пароле'),
        description = 'Пароль'),
    form.Textbox('remote_ip_address', description = 'Адрес в локальной сети'))

outForm = form.Form(
    form.Textbox('user',
        form.Validator('* Длина имени не должна превышать 12 символов', 
            lambda i: len(i) <= 12 ),
        form.regexp(REGEXP, '* Недопустимые символы в имени'),
        description = 'Логин'),
    form.Textbox('user_password',
        form.Validator('* Длина пароля не должна превышать 12 символов', 
            lambda i: len(i) <= 12 ),
        form.regexp(REGEXP, '* Недопустимые символы в пароле'),
        description = 'Пароль'))


class Network:
    def __init__(self):
        # значения по умолчанию 
        self.net_conf = {'ip_address': '', 'netmask': '', 'gateway': ''}
        self.mgetty_conf = {'port': '', 'speed': '38400', 'init-chat': '', 
            'debug': '4', 'rings': RINGS[0]}
        self.ppp_conf = {'port': '', 'speed': '38400', 'debug': False, 
        'remotename': '', 'remote_password': '', 'remote_ip_address': '',
        'user': '', 'user_password': ''}

        self._ethParams()
        self._mgettyConf()
        self._pppConf()

    def _ethParams(self):
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
        self.net_conf['ip_address'] = config_eth0[0] 
        self.net_conf['netmask'] = config_eth0[2] 
        self.net_conf['gateway'] = routes_eth0[2]
    
    def _mgettyConf(self):
        '''
        mgetty.conf д.б. упрощенной структуры с одной секцией:
        port ttyS<N> #начало секции
        speed PORT_SPEED
        init-chat "" AT<1> OK ... AT<N> OK
        debug 4 #до 9
        rings 1 #99 - не отвечать

        '''
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
                    self.mgetty_conf[line[0]] = ' '.join(line[1:])
                elif line[0] == 'port':
                    section = True
                    self.mgetty_conf[line[0]] = ' '.join(line[1:])

    def _pppConf(self):
        '''
        Пример файла /etc/pppd/options:
        lock
        38400
        /dev/ttyS2
        debug
        
        Берется port и speed        
        '''
        patt = '/dev/ttyS'
        with open(PPPD_OPTIONS_PATH) as mc:
            for line in mc:
                line = line.strip()
                if line[0:len(patt)] == patt:
                    self.ppp_conf['port'] = line
                elif line in BAUD_RATES:
                    self.ppp_conf['speed'] = line
                elif line == 'debug':
                    self.ppp_conf['debug'] = True

        '''
        Пример chap-secrets:
            "recorder"  *   recorder_password   -
            client    *   "client password"   192.168.1.29:192.168.1.200
        FIXME!!! Для упрощения двойные кавычки допускаются только
        для сплошных полей. Логины и пароли д.б. в формате ^[0-9a-zA-Z_]*$:
            recorder  *   ""                -
            client    *   "client_password"   192.168.1.29:192.168.1.200

        '''
        with open(PPPD_CHAP_SECRETS_PATH) as mc:
            for line in mc:
                line = line.strip()
                if line and line[0] != '#':
                    line = line.split()
                    line = [l.strip('"') for l in line]
                    if len(line) != 4:
                        continue
                    if line[3] == '-':
                        self.ppp_conf['user'] = line[0]
                        self.ppp_conf['user_password'] = line[2]
                    else:
                        self.ppp_conf['remotename'] = line[0]
                        self.ppp_conf['remote_password'] = line[2]
                        self.ppp_conf['remote_ip_address'] = \
                            line[3].split(':')[1] if ':' in line[3] else ''


    def _comPorts(self):
        '''
        Список портов формируется из объединения след. множеств:
        1. устройства, указанного в mgetty.config
        2. послед. портов, показанных setserial и занятых/ответивших pppd 
        return <список>, <текущий_порт>
        <текущий_порт> = 0 = порт не задан
        например:
        (1, 4), 1 - (COM1, COM4), где COM1 текущий

        '''
        ports = []
        cur_port = 0
        
        # 1.
        if self.mgetty_conf['port']:
            cur_port = int(self.mgetty_conf['port'][-1]) + 1
            ports.append(cur_port)

        # 2. Проверки слизаны из pppconfig.real
        if DEBUG_PATH:
            par = ['cat', DEBUG_PATH + '/setserial.out']
            busy = True
        else:
            par = ['setserial', '-g']
            for i in xrange(4):
                par.append('/dev/ttyS%d' % i)
            busy = not call(['pidof', 'pppd'])

        ttyS = Popen(par, stdout = PIPE).communicate()[0].split('\n')
        for t in ttyS:
            if re.search('16[45]50', t):
                tt = re.search('/dev/ttyS[1-4]', t)
                if tt:
                    tt = tt.group()
                    if not busy:
                        pppdRet = Popen(['pppd', 'nodetach', 'noauth', 
                            'nocrtscts', tt, 'connect', 
                            "chat -t1 '' AT OK"], 
                            stdout = PIPE).communicate()[0]
                        
                        if 'established' not in pppdRet:
                            continue
                    tt = int(tt[-1]) + 1
                    if tt not in ports:
                        ports.append(tt)
        
        ports.sort()
        return ports, cur_port

    def _answer(self, istr, strip=True):
        '''
        Удаление/добавление ожидаемых от модема ответов на команды
        инициализации. Команда ATZ OK убирается/добавляется.
        '"" ATZ OK AT<cmd2> OK ... AT<cmdN> OK' <=> 'AT<cmd2> ... AT<cmdN>'
        '''
        if strip:
            # Удаление
            if istr:
                istr = ' '.join([i for i in istr.split()\
                    if i != '""' and i != 'OK' and i != 'ATZ']) 
        else:
            # Добавление
            istr = '"" ATZ OK ' + ' '.join([i+' OK' for i in istr.split()])
        return istr

    def GET(self):
        nocache()

        ethFrm = ethForm()
        for i in ('ip_address', 'netmask', 'gateway'):
            ethFrm[i].set_value(self.net_conf[i])

        mdmFrm = modemForm()
        ports, cur_port = self._comPorts()
        # если порты модемов mgetty и pppd не совпадают
        # считается, что модем не задан
        if self.mgetty_conf['port'] not in self.ppp_conf['port']:
            cur_port = 0
        pp = [COM_PORTS[0],]
        for i in ports:
            pp.append(COM_PORTS[i])
        mdmFrm['port'].args = pp
        modemForm['port'].args = pp
        mdmFrm['port'].set_value(COM_PORTS[cur_port])
        mdmFrm['init-chat'].set_value(
            self._answer(self.mgetty_conf['init-chat']))
        mdmFrm['debug'].set_value(self.mgetty_conf['debug'])
        mdmFrm['speed'].set_value(self.mgetty_conf['speed'])

        inFrm = inForm()
        if self.mgetty_conf['rings'] in RINGS:
            inFrm['rings'].set_value(self.mgetty_conf['rings'])
        for i in ('remotename', 'remote_password', 'remote_ip_address'):
            inFrm[i].set_value(self.ppp_conf[i])

        outFrm = outForm()
        for i in ('user', 'user_password'):
            outFrm[i].set_value(self.ppp_conf[i])


        return render.network(ethFrm, mdmFrm, inFrm, outFrm, title = title)

    def _checkIp(self, ip):
        '''
        Проверка адреса.
        Дополнительно к IP отсекаются короткие адреса
        и адреса с маской (напр.: 127.0, 127.0.0.0/8)
        '''
        if '/' not in ip and len(ip.split('.')) == 4:
            try:
                IP(ip)
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
        if ip == gateway:
            return False
        if gateway:
            ip1 = IP(ip + '/' + netmask, make_net=True)
            ip2 = IP(gateway + '/' + netmask, make_net=True)
            if ip1.ip != ip2.ip:
                return False
        return True

    def _writeNetConf(self):
        config = ConfigObj(NET_CONFIG_PATH, list_values = False)
        config['config_eth0'] = '"%s netmask %s"' % \
            (self.net_conf['ip_address'], self.net_conf['netmask'])
        config['routes_eth0'] = '"default via %s"' % self.net_conf['gateway']
        config.write()


    def _writeMgettyConf(self):
        '''
        mgetty.conf полностью переписывается
        '''
        l = []
        if self.mgetty_conf['port']:
            # сначала порт
            l.append('port ' + self.mgetty_conf['port'] + '\n')
            for k, v in self.mgetty_conf.iteritems(): 
                if k != 'port':
                    l.append(k + ' ' + v + '\n')
        rewrite(MGETTY_CONF_PATH, l)

    def _restartMgetty(self):
        # проверить есть ли mgetty в inittab
        exist = False
        with open(INITTAB_PATH) as it:
            for l in it:
                l = l.strip()
                if l and l[0] != '#' and MGETTY_INITTAB in l:
                    exist = True

        if exist:
            if self.mgetty_conf['port']:
                # заменить tty
                call(['sed', '-i', 
                    '{s%^' + MGETTY_INITTAB + '.*$%' + MGETTY_INITTAB + ' ' + self.mgetty_conf['port'] + '%}', INITTAB_PATH])
            else:
                # FIXME удалить строку, а не заменить на пустую 
                # удалить mgetty 
                call(['sed', '-i', 
                    '{s%^' + MGETTY_INITTAB + '.*$%%}', INITTAB_PATH])
        else:
            # добавить сервис
            l = '\n' + MGETTY_INITTAB + ' ' + self.mgetty_conf['port'] + '\n'
            with open(INITTAB_PATH, 'a') as it:
                it.write(l)
        
        # перезапуск mgetty
        if not DEBUG_PATH:
            call(['/sbin/telinit', 'q'])

    def _writePppConf(self):
        '''
        Переписывет файлы:
            /etc/ppp/otions
            /etc/ppp/chap-secrets
        В файле /etc/chatscripts/outgouing
        меняется 2-я строка - строка инициализации модема
        '''
        # /etc/ppp/options
        l = ['lock\n',]
        for i in ('port', 'speed'):
            l.append(self.ppp_conf[i] + '\n')
        if self.ppp_conf['debug']:
            l.append('debug\n')
        rewrite(PPPD_OPTIONS_PATH, l)
        del l
        
        # /etc/ppp/chap-secrets
        #    user  *   user_password                -
        #    remotename    *   remote_password   ip_address:remote_ip_address
        l = []
        l.append('"' + self.ppp_conf['user'] + '"\t*\t"' + \
            self.ppp_conf['user_password'] + '"\t-\n')
        l.append('"' + self.ppp_conf['remotename'] + '"\t*\t"' + \
            self.ppp_conf['remote_password'] + '"\t' + \
            self.net_conf['ip_address'] + ':' + \
            self.ppp_conf['remote_ip_address'] + '\n')
        rewrite(PPPD_CHAP_SECRETS_PATH, l)

        # /etc/chatscripts/outgouing
        call(['sed', '-i', 
            '{s/^"" ATZ.*$/'+ self.mgetty_conf['init-chat'] + '/}', OUTGOUING_CHATSCRIPT_PATH])
 
    def POST(self):
        ethFrm = ethForm()
        mdmFrm = modemForm()
        inFrm = inForm()
        outFrm = outForm()
        ethValid = ethFrm.validates()
        mdmValid = mdmFrm.validates()
        inValid = inFrm.validates()
        outValid = outFrm.validates()

        # считать все данные и привести к нужному виду
        net = {}
        mgetty = {}
        ppp = {}

        for k in ('ip_address', 'netmask', 'gateway'):
            net[k] = ethFrm[k].get_value().strip()

        for k in ('port', 'speed', 'init-chat'):
            mgetty[k] = mdmFrm[k].get_value()
        
        # добавить ответы модема 
        mgetty['init-chat'] = self._answer(mgetty['init-chat'], strip=False)
      
        i = COM_PORTS.index(mgetty['port'])
        mgetty['port'] = 'ttyS' + str(i - 1) if i else ''
        
        mgetty['rings'] = inFrm['rings'].get_value()
        if mgetty['rings'] == RINGS[0]:
            mgetty['rings'] = '99'

        for k in ('remotename', 'remote_password', 'remote_ip_address'):
            ppp[k] = inFrm[k].get_value().strip()
        for k in ('user', 'user_password'):
            ppp[k] = outFrm[k].get_value().strip()

        ppp['port'] = '/dev/' + mgetty['port'] if mgetty['port'] else ''

        if ethValid:
            ethValid = self._checkNetmask(net['ip_address'], net['netmask'])
            if not ethValid:
                ethFrm['netmask'].note = NOTE_INVALID_VALUE
            else:
                ethValid = self._checkGateway(net['ip_address'], 
                    net['netmask'], net['gateway'])
                if not ethValid:
                    ethFrm['gateway'].note = NOTE_INVALID_VALUE
        if mgetty['port']:
            if mgetty['rings'] != '99':
                for i in ('remotename', 'remote_password', 'remote_ip_address'):
                    if not ppp[i]:
                        inFrm[i].note = NOTE_NO_VALUE
                        inValid = False

            for i in ('user', 'user_password'):
                if not ppp[i]:
                    outFrm[i].note = NOTE_NO_VALUE
                    outValid = False

        if ppp['remote_ip_address'] and\
            not self._checkGateway(net['ip_address'], 
                net['netmask'], ppp['remote_ip_address']):
            inFrm['remote_ip_address'].note = NOTE_INVALID_VALUE
            inValid = False

        
        if not ethValid or not mdmValid or not inValid or not outValid:
            return render.network(ethFrm, mdmFrm, inFrm, outFrm, title = title)
       
        net_changed = False
        for k, v in net.iteritems():
            if self.net_conf[k] != v:
                net_changed = True
                break

        mgetty_changed = False
        for k, v in mgetty.iteritems():
            if self.mgetty_conf[k] != v:
                mgetty_changed = True
                break

        ppp_changed = False
        for k, v in ppp.iteritems():
            if self.ppp_conf[k] != v:
                ppp_changed = True
                break

        if net_changed:
            self.net_conf.update(net)
            self._writeNetConf()
            service('eth0', 'restart')

        if mgetty_changed:
            self.mgetty_conf.update(mgetty)
            self._writeMgettyConf()
            self._restartMgetty()
        
        if ppp_changed:
            self.ppp_conf.update(ppp)
            self._writePppConf()

        return render.completion(title)
