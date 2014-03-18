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
        IP адрес удаленного клиента
        IP адрес регистратора
    
    Исходящие подключения.
        Логин
        Пароль

При входящем подключении используются заданные адреса

При исходящем подключении регистратор всегда использует
один и тот же логин и пароль, а адрес получает от удаленного
сервера.

Если модем не задан, остальные параметры могут быть пустыми, иначе
производится проверка как обычно.

Пример. Настройка интернет мегафона
1. Строка инициализации с установкой APN
AT+CGDCONT=1,"IP","internet"
2. Номер телефона
*99***1#
3. Пользователь и пароль - пустые(любые?)
'''
from web import form
from config import render, DEBUG_PATH
from utils import restart_service, rewrite2 
from http import nocache
from configobj import ConfigObj
from IPy import IP
from subprocess import Popen, PIPE, call
import re
from os import walk, mkdir
from os.path import exists

NET_CONFIG_PATH = DEBUG_PATH + '/etc/conf.d/net'
RESOLV_CONF_PATH = DEBUG_PATH + '/etc/resolv.conf'
MGETTY_CONFIG_PATH = DEBUG_PATH + '/etc/mgetty+sendfax/mgetty.config'
LOGIN_CONFIG_PATH = DEBUG_PATH + '/etc/mgetty+sendfax/login.config'
INITTAB_PATH = DEBUG_PATH + '/etc/inittab'
PPPD_OPTIONS_PATH = DEBUG_PATH + '/etc/ppp/options'
PPPD_CHAP_SECRETS_PATH = DEBUG_PATH + '/etc/ppp/chap-secrets'
PPPD_PAP_SECRETS_PATH = DEBUG_PATH + '/etc/ppp/pap-secrets'
PPPD_PAP_SECRETS_PATH = DEBUG_PATH + '/etc/ppp/pap-secrets'
INCOMING_OPTIONS_PATH = DEBUG_PATH + '/etc/ppp/peers/incoming'
OUTGOING_OPTIONS_PATH = DEBUG_PATH + '/etc/ppp/peers/outgoing'
CHATSCRIPTS_PATH = DEBUG_PATH + '/etc/ppp/chatscripts'
OUTGOING_CHATSCRIPTS_PATH = CHATSCRIPTS_PATH + '/outgoing'
DEV_PATH = DEBUG_PATH + '/dev'

title = 'Настройка сети'
NOTE_INVALID_VALUE = 'Неверное значение'
MGETTY_INITTAB = 'm1:2345:respawn:/sbin/mgetty'
MGETTY_DEBUG_LVL_MAX = 9
BAUD_RATES = ['2400', '4800', '9600', '19200', '38400', '57600']
REGEXP = '^[0-9a-zA-Z_]*$'
RINGS = [u'Нет'] + [str(i) for i in xrange(1, 8)]
NOTE_NO_VALUE = 'Значение не задано'

ethForm = form.Form(
    form.Textbox('ip_address', 
        form.Validator('Не заполнено', bool),
        description = 'IP адрес'),
    form.Textbox('netmask', 
        form.Validator('Не заполнено', bool),
        description = 'Маска сети'),
    form.Textbox('gateway', description = 'Шлюз'),
    form.Textbox('dns', description = 'DNS'),
    )

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
    form.Textbox('remote_ip_address', description = 'Адрес удаленного компьютера'),
    form.Textbox('local_ip_address', description = 'Адрес регистратора'),
    )

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
        self.net_conf = {'ip_address': '', 'netmask': '', 'gateway': '', 
            'dns': ''}
        self.mgetty_conf = {'port': '', 'speed': '57600', 'init-chat': '', 
            'debug': '', 'rings': RINGS[0]}
        self.ppp_conf = {'port': '', 'speed': '57600', 'debug': False, 
        'remotename': '', 'remote_password': '', 'remote_ip_address': '',
        'local_ip_address': '', 'user': '', 'user_password': ''}

        self._ethParams()
        self._mgettyConf()
        self._pppConf()

    def _ethParams(self):
        '''
        Читает NET_CONFIG_PATH и возвращает 
        IP-адрес, маску сети, адрес шлюза и DNS.
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
        if len(routes_eth0) > 2:
            self.net_conf['gateway'] = routes_eth0[2]
        
        with open(RESOLV_CONF_PATH) as rc:
            for line in rc:
                line = line.strip()
                if not line or line[0] == '#':
                    continue
                line = line.split()
                if len(line) < 2 or line[0] != 'nameserver':
                    continue
                self.net_conf['dns'] = line[1]

    
    def _mgettyConf(self):
        '''
        mgetty.conf д.б. упрощенной структуры с одной секцией:
        port tty<> #начало секции
        speed PORT_SPEED
        init-chat "" AT<1> OK ... AT<N> OK
        debug 4 #до 9
        rings 1 #99 - не отвечать

        '''
        section = False
        with open(MGETTY_CONFIG_PATH) as mc:
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
        with open(PPPD_OPTIONS_PATH) as mc:
            for line in mc:
                line = line.strip()
                if line[5:-1] in ('ttyS', 'ttyUSB', 'ttyACM'):
                    self.ppp_conf['port'] = line
                elif line in BAUD_RATES:
                    self.ppp_conf['speed'] = line
                elif line == 'debug':
                    self.ppp_conf['debug'] = True

        '''
        Пример chap-secrets/pap-secrets:
            "recorder"  *   recorder_password   *
            client    *   "client password"     *
        FIXME!!! Для упрощения двойные кавычки допускаются только
        для сплошных полей. Логины и пароли д.б. в формате ^[0-9a-zA-Z_]*$:
            recorder  *   ""                    *
            client    *   "client_password"     *

        '''
        with open(PPPD_CHAP_SECRETS_PATH) as mc:
            user = True
            for line in mc:
                line = line.strip()
                if line and line[0] != '#':
                    line = line.split()
                    line = [l.strip('"') for l in line]
                    if len(line) != 4:
                        continue
                    if user:
                        self.ppp_conf['user'] = line[0]
                        self.ppp_conf['user_password'] = line[2]
                        user = False 
                    else:
                        self.ppp_conf['remotename'] = line[0]
                        self.ppp_conf['remote_password'] = line[2]
        
        # Адреса из /etc/ppp/peers/incoming
        try:
            with open(INCOMING_OPTIONS_PATH) as io:
                for line in io:
                    if ':' in line:
                        line = line.split(':')
                        self.ppp_conf['local_ip_address'] = line[0]
                        self.ppp_conf['remote_ip_address'] = line[1]
        except:
            pass

    def _tty_com(self, tty, com):
        '''
        Возвращает  tty по com или com по tty,
        неизвестный д.б. равен None:
        '', 'Нет'
        'ttyS0', 'COM1'
        ...
        'ttyUSB0', 'USB-COM0'
        ...
        'ttyACM0', 'USB0'
        ...
        '''
        if tty == None:
            if com == u'Нет':
                tty = ''
            elif com[:3] == 'COM':
                tty = 'ttyS'+ str(int(com[3])-1)
            elif com[:4] == 'USB-':
                tty = 'ttyUSB' + com[7]
            else:
                tty = 'ttyACM' + com[3]
            return tty
        else:
            if tty == '':
                com = u'Нет'
            elif tty[3] == 'S':
                com = 'COM' + str(int(tty[4])+1)
            elif tty[3] == 'U':
                com = 'USB-COM' + tty[6]
            elif tty[3] == 'A':
                com = 'USB' + tty[6]
            return com



    def _comPorts(self):
        '''
        Список портов формируется из 
        послед. портов ttyS<номер>, ttyUSB<номер>, ttyACM<номер>
        существующих в /dev устройств и занятых/ответивших pppd.
        Проверки слизаны из pppconfig.real.

        return <список>, <текущий_порт>
        <текущий_порт> = '' = порт не задан
        например:
        (ttyS1, ttyUSB0), ttyS1 - (COM2, USB-COM0), COM2
        '''
        all_ports = []
        ports = ['']
        
        cur_port = self.mgetty_conf['port']
        # если порты модемов mgetty и pppd не совпадают
        # считается, что модем не задан
        if cur_port not in self.ppp_conf['port']:
            cur_port = ''
        
        for r,d,f in walk(DEV_PATH):
            if r == DEV_PATH:
                for ff in f:
                    if ff.find('ttyS', 0) == 0 or ff.find('ttyUSB', 0) == 0 or ff.find('ttyACM', 0) == 0:
                        all_ports.append(ff)
        
        if DEBUG_PATH:
            ports += all_ports
        else:
            busy = not call(['pidof', 'pppd'])
            for t in all_ports:
                if t == cur_port and busy:
                    continue
                pppdRet = Popen(['/usr/sbin/pppd', 'nodetach', 
                    'nocrtscts', t, 'connect', "chat -t 1 '' AT OK",
                    'lcp-max-configure', '1'],
                    stdout = PIPE).communicate()[0]
                
                if 'established' not in pppdRet:
                    continue
                ports.append(t)

        if cur_port not in ports:
            ports.append(cur_port)

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
        for i in ('ip_address', 'netmask', 'gateway', 'dns'):
            ethFrm[i].set_value(self.net_conf[i])

        mdmFrm = modemForm()
        ports, cur_port = self._comPorts()
        pp = []
        for i in ports:
            pp.append(self._tty_com(i, None))
        mdmFrm['port'].args = pp
        modemForm['port'].args = pp
        mdmFrm['port'].set_value(self._tty_com(cur_port, None))
        mdmFrm['init-chat'].set_value(
            self._answer(self.mgetty_conf['init-chat']))
        mdmFrm['debug'].set_value(self.mgetty_conf['debug'])
        mdmFrm['speed'].set_value(self.mgetty_conf['speed'])

        inFrm = inForm()
        if self.mgetty_conf['rings'] in RINGS:
            inFrm['rings'].set_value(self.mgetty_conf['rings'])
        for i in ('remotename', 'remote_password', 'remote_ip_address', 
                'local_ip_address'):
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
        #config = ConfigObj(NET_CONFIG_PATH, list_values = False)
        #config['config_eth0'] = '"%s netmask %s"' % \
        #    (self.net_conf['ip_address'], self.net_conf['netmask'])
        #config['routes_eth0'] = '"default via %s"' % self.net_conf['gateway']
        #config.write()
        l = ['config_eth0="%s netmask %s"\n' % \
            (self.net_conf['ip_address'], self.net_conf['netmask']),
            'routes_eth0="default via %s"' % self.net_conf['gateway']]
        rewrite2(NET_CONFIG_PATH, l)
        rewrite2(RESOLV_CONF_PATH, ['nameserver %s' % (self.net_conf['dns'])])


    def _writeMgettyConfig(self):
        '''
        mgetty.conf полностью переписывается
        '''
        l = ['modem-type data\n']
        if self.mgetty_conf['port']:
            # сначала порт
            l.append('port ' + self.mgetty_conf['port'] + '\n')
            for k, v in self.mgetty_conf.iteritems(): 
                if k != 'port' and v:
                    l.append(k + ' ' + v + '\n')
        rewrite2(MGETTY_CONFIG_PATH, l)

    def _writeLoginConfig(self):
        '''
        login.config полностью переписывается
        '''
        l = []
        if self.mgetty_conf['rings'] != 99:
            # Принимать входящие подключения
            l.append('/AutoPPP/ -    a_ppp   /usr/sbin/pppd call incoming\n')
        rewrite2(LOGIN_CONFIG_PATH, l)

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
            l = '\n' + MGETTY_INITTAB + ' ' + self.mgetty_conf['port']
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
            /etc/ppp/peers/incoming
        В файле /etc/ppp/chatscripts/outgouing
        меняется 2-я строка - строка инициализации модема
        '''
        # /etc/ppp/options
        l = ['lock\n', 'crtscts\n',]
        for i in ('port', 'speed'):
            l.append(self.ppp_conf[i] + '\n')
        if self.ppp_conf['debug']:
            l.append('debug\n')
        rewrite2(PPPD_OPTIONS_PATH, l)
        del l

        
        # /etc/ppp/chap-secrets
        #    user  *   user_password            *
        #    remotename    *   remote_password  *
        l = []
        l.append('*\t*\t""\n')
        l.append('"' + self.ppp_conf['user'] + '"\t*\t"' + \
            self.ppp_conf['user_password'] + '"\t*\n')
        l.append('"' + self.ppp_conf['remotename'] + '"\t*\t"' + \
            self.ppp_conf['remote_password'] + '"\t*\n')
        rewrite2(PPPD_CHAP_SECRETS_PATH, l)
        rewrite2(PPPD_PAP_SECRETS_PATH, l)

        # /etc/ppp/peers/incoming
        l = ['auth\n', 'require-mschap-v2\n']
        l.append(self.ppp_conf['local_ip_address'] + ':' + self.ppp_conf['remote_ip_address'] + '\n')
        rewrite2(INCOMING_OPTIONS_PATH, l)

        # /etc/ppp/peers/outgouing
        rewrite2(OUTGOING_OPTIONS_PATH, 
            ['noauth\n', 
            'connect "/usr/sbin/chat -v -f /etc/ppp/chatscripts/outgoing"\n',
            'defaultroute\n',
            'noipdefault\n',
            'ipcp-accept-local\n',
            'ipcp-accept-remote\n',
            'usepeerdns\n',
            'user ' + self.ppp_conf['user']])
        
        # /etc/ppp/chatscripts/outgouing
        if not exists(CHATSCRIPTS_PATH):
            mkdir(CHATSCRIPTS_PATH)
        # 1. строка - реакция на ошибки
        l = ["ABORT BUSY ABORT ERROR ABORT 'NO ANSWER' ABORT 'NO CARRIER' ABORT 'NO DIALTONE'\n",
        # 2. строка инициализации
            self.mgetty_conf['init-chat'] + '\n',
        # 3. номер телефона
            "'ATD'\n",
        # 4. таймаут
            "TIMEOUT 30\n",
        # 5. connect
            "CONNECT\n"]
        rewrite2(OUTGOING_CHATSCRIPTS_PATH, l)
 
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

        for k in ('ip_address', 'netmask', 'gateway', 'dns'):
            net[k] = ethFrm[k].get_value().strip()

        for k in ('port', 'speed', 'init-chat', 'debug'):
            mgetty[k] = mdmFrm[k].get_value()
        
        # добавить ответы модема 
        mgetty['init-chat'] = self._answer(mgetty['init-chat'], strip=False)
      
        mgetty['port'] = self._tty_com(None, mgetty['port'])
        
        mgetty['rings'] = inFrm['rings'].get_value()
        if mgetty['rings'] == RINGS[0]:
            mgetty['rings'] = '99'

        if mgetty['debug']:
            mgetty['debug'] = '4'
            ppp['debug'] = True
        else:
            ppp['debug'] = False

        for k in ('remotename', 'remote_password', 'remote_ip_address',
                'local_ip_address'):
            ppp[k] = inFrm[k].get_value().strip()
        for k in ('user', 'user_password'):
            ppp[k] = outFrm[k].get_value().strip()

        ppp['port'] = '/dev/' + mgetty['port'] if mgetty['port'] else ''
        ppp['speed'] = mgetty['speed']

        if ethValid:
            ethValid = self._checkNetmask(net['ip_address'], net['netmask'])
            if not ethValid:
                ethFrm['netmask'].note = NOTE_INVALID_VALUE

            if not self._checkGateway(net['ip_address'], net['netmask'],
                net['gateway']):
                ethValid = False
                ethFrm['gateway'].note = NOTE_INVALID_VALUE
            if net['dns'] and not self._checkIp(net['dns']):
                ethValid = False
                ethFrm['dns'].note = NOTE_INVALID_VALUE
            
        if mgetty['port']:
            if mgetty['rings'] != '99':
                for i in ('remotename', 'remote_password', 'remote_ip_address',
                        'local_ip_address'):
                    if not ppp[i]:
                        inFrm[i].note = NOTE_NO_VALUE
                        inValid = False

            for i in ('user', 'user_password'):
                if not ppp[i]:
                    outFrm[i].note = NOTE_NO_VALUE
                    outValid = False

        if ppp['remote_ip_address'] or ppp['local_ip_address']:
            if not ppp['remote_ip_address']:
                inFrm['remote_ip_address'].note = NOTE_INVALID_VALUE
                inValid = False
            elif not ppp['local_ip_address']:
                inFrm['local_ip_address'].note = NOTE_INVALID_VALUE
                inValid = False
            elif not self._checkGateway(ppp['local_ip_address'], 
                '255.255.255.0', ppp['remote_ip_address']):
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
            restart_service('eth0')
            restart_service('ntpd')

        if mgetty_changed:
            self.mgetty_conf.update(mgetty)
            self._writeMgettyConfig()
            self._writeLoginConfig()
            self._restartMgetty()
        
        if ppp_changed:
            self.ppp_conf.update(ppp)
            self._writePppConf()

        return render.completion(title)
