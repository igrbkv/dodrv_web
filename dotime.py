# -*- coding: utf-8 -*-
'''
Форма:
Установка временной зоны.
    Зона
    
Установка даты и времени.
    Вручную
        [1] [янв] [1970] [00]:[00]
    По GPS
        Порт [COM1-4]
    По сети
        IP cервер времени

Год: диапазон от текущего -1+10, но не меньше 1970

Часовые зоны:
/usr/share/zoneinfo/Europe/
    Kaliningrad     UTC+3
    Moscow          UTC+4
/usr/share/zoneinfo/Asia/
    Yekaterinburg   UTC+6
    Omsk            UTC+7
    Krasnoyarsk     UTC+8
    Irkutsk         UTC+9
    Yakutsk         UTC+10
    Vladivostok     UTC+11
    Magadan         UTC+12
cp /usr/share/zoneinfo/<Зона> /etc/localtime
echo <Зона> > /etc/timezone

1. При ручной установке
останавливаются и удаляются сервисы
/etc/init.d/ntp-client
/etc/init.d/ntp-pps
/etc/init.d/ntpd


2. При установке синхронизации по серверу времени 

останавливается и удаляется сервис
/etc/init.d/ntp-pps

изменяются след. файлы:

    /etc/conf.d/ntp-client
# sntp используется для грубой установки времени при загрузке системы. 
NTPCLIENT_CMD="sntp"
NTPCLIENT_OPTS="-p -s -t 10 <ip_address, напр. ntp1.vniiftri.ru>"

    /etc/conf.d/ntpd.conf
#NTPD_OPTS="-u ntp:ntp" - Run as userid (or userid:groupid)
NTPD_OPTS=""
    /etc/ntp.conf
server <ip_address, напр. ntp1.vniiftri.ru>
#fudge ...

устанавливаются и перезапускаются сервисы:
/etc/init.d/ntp-client
/etc/init.d/ntpd

3. При установке синхронизации по GPS 
    /etc/conf.d/ntp-client
# sntp используется для грубой установки времени при загрузке системы. 
NTPCLIENT_CMD="sntp"
NTPCLIENT_OPTS="-p -s -t 10 127.127.20.<N>"

изменяются след. файлы:
    /etc/conf.d/ntp-pps
NTP_PPS_DEVICE="/dev/ttyS<N>"

    /etc/conf.d/ntpd.conf
#NTPD_OPTS="-u ntp:ntp" - Run as userid (or userid:groupid)
NTPD_OPTS=""

    /etc/ntp.conf
# NMEA Parma GPS with PPSAPI(flag1 1)
server 127.127.20.<N> prefer
fudge 127.127.20.<N>  flag1 1 flag3 1

где <N> - номер устройства, напр. ttyS1 => COM2

устанавливаются и перезапускаются сервисы 
/etc/init.d/ntp-client
/etc/init.d/ntp-pps
/etc/init.d/ntp

'''
from web import form
from config import render, DEBUG_PATH
from utils import add_service, del_service, sync_mode 
from http import nocache
from configobj import ConfigObj
from IPy import IP
from subprocess import Popen, PIPE, call
import re
from time import localtime
from datetime import date

NTP_PPS_PATH = DEBUG_PATH + '/etc/conf.d/ntp-pps'
NTP_CLIENT_PATH = DEBUG_PATH + '/etc/conf.d/ntp-client'
NTPD_PATH = DEBUG_PATH + '/etc/conf.d/ntpd'
NTP_CONF_PATH = DEBUG_PATH + '/etc/ntp.conf'
TIMEZONE_PATH = DEBUG_PATH + '/etc/timezone'
LOCALTIME_PATH = DEBUG_PATH + '/etc/localtime'

title = 'Настройка времени'
TZBASEPATH = '/usr/share/zoneinfo/'
TIMEZONES = (   
    ('', 'Нет'),
    ('Europe/Kaliningrad', 'Калининград (UTC+3)'),
    ('Europe/Moscow',      'Москва (UTC+4)'),
    ('Asia/Yekaterinburg', 'Екатеринбург (UTC+6)'),
    ('Asia/Omsk',          'Омск (UTC+7)'),
    ('Asia/Krasnoyarsk',   'Красноярск (UTC+8)'),
    ('Asia/Irkutsk',       'Иркутск (UTC+9)'),
    ('Asia/Yakutsk',       'Якутск (UTC+10)'),
    ('Asia/Vladivostok',   'Владивосток (UTC+11)'),
    ('Asia/Magadan',       'Магадан (UTC+12)'))

MONTHS = [u'', u'янв', u'фев', u'мар', u'апр', u'май', u'июн', u'июл', u'авг', 
    u'сен', u'окт', u'ноя', u'дек']
DAYS = [''] + [str(i) for i in xrange(1, 32)]
HOURS = [''] + [str(i) for i in xrange(24)]
MINUTES = [''] + [str(i) for i in xrange(60)]

NOTE_INVALID_VALUE = 'Неверное значение'
NOTE_NO_VALUE = 'Значение не задано'
COM_PORTS = [u'Нет', 'COM1', 'COM2', 'COM3', 'COM4']

tzForm = form.Form(
    form.Dropdown('tz', TIMEZONES, description = 'Зона'))

# FIXME modeForm и modeFrms - суть одно и то же
# modeForm используется для чтения данных от клиента
# modeFrms при выводе для разбиения списка на отдельные строки см. dotime.html
modeForm = form.Form(
    form.Radio('', 
        [('manually', 'Установка вручную'),
        ('gps', 'Установка по GPS'),
        ('ntp', 'Установка по серверу времени')]))

modeForms = \
    [form.Form(form.Radio('', [('manually', 'Установка вручную'),])),
    form.Form(form.Radio('', [('gps', 'Установка по GPS'),])),
    form.Form(form.Radio('', [('ntp', 'Установка по серверу времени'),]))]

timeForm = form.Form(
    form.Dropdown('day', DAYS, description = 'День'),
    form.Dropdown('month', MONTHS, description = 'Месяц'),
    form.Dropdown('year', [], description = 'Год'),
    form.Dropdown('hour', HOURS, description = 'Час'),
    form.Dropdown('minute', MINUTES, description = 'Минута'),
    validators = [form.Validator(NOTE_INVALID_VALUE, 
        lambda i: i.day and i.month and i.year and i.hour and i.minute)])

gpsForm = form.Form(    
    form.Dropdown('port', [], description = 'COM порт'))

ntpForm = form.Form(
    form.Textbox('server_address', description = 'Адрес'))

def years(year):
    year = 1970 if year <= 1970 else year
    return [str(i) for i in xrange(year - 1, year + 11)]


def addressValid(adr):
    '''
    Проверка адреса.
    1. IP-адрес
    2. URL
    '''
    adr = adr.strip()
    t = re.match('[0-9.]+', adr)
    if t and len(adr.split('.')) == 4:
        try:
            IP(adr)
            return True
        except:
            pass
    if re.match('[0-9a-z.-_]+', adr):
        return True
    
    return False

def comPorts():
    '''
    Список портов формируется из
    послед. портов, показанных setserial 
    
    return <список>
    например (1, 4) #(COM1, COM4)
    '''
    ports = []
    # Проверки слизаны из pppconfig.real
    if DEBUG_PATH:
        par = ['cat', DEBUG_PATH + '/setserial.out']
    else:
        par = ['setserial', '-g']
        for i in xrange(4):
            par.append('/dev/ttyS%d' % i)

    ttyS = Popen(par, stdout = PIPE).communicate()[0].split('\n')
    for t in ttyS:
        if re.search('16[45]50', t):
            tt = re.search('/dev/ttyS[1-4]', t)
            if tt:
                tt = tt.group()
                tt = int(tt[-1]) + 1
                if tt not in ports:
                    ports.append(tt)
    
    ports.sort()
    return ports

def curPort():
    '''
    Текущий СОМ-порт
    
    return  0   - нет
            <N> - COM<N>
    '''
    try:
        config = ConfigObj(NTP_PPS_PATH)
        return int(config['NTP_PPS_DEVICE'][-1])
    except:
        return 0

def curZone():
    '''
    '''
    data = ''
    try:
        with open(TIMEZONE_PATH, 'r') as f:
            data = f.read(80)
    except:
        pass
    return data.strip()

def serverAddress():
    '''
    Адрес берется из первой строки вида:
    server <address> ...
    '''
    adr = ''
    with open(NTP_CONF_PATH, 'r') as f:
        s = f.readline()
        while s:
            t = re.search('(?<=^server\s)\s*\S+.*$', s)
            if t:
                adr = t.group().split()[0]
                break
            s = f.readline()
    return adr

def dateValid(year, month, day):
    try:
        date(year, month, day)
    except:
        return False
    return True

def setTimezone(tz):
    with open(TIMEZONE_PATH, 'w') as f:
        f.write(tz)

def setDatetime(year, month, day, hour, minute):
    # MMDDhhmm[[CC]YY
    ds = '%02d%02d%02d%02d%04d' % (month, day, hour, minute, year)
    call(['date', ds])

def setPort(port):
    with open(NTP_PPS_PATH, 'w') as f:
        f.write('NTP_PPS_DEVICE="/dev/ttyS%d"'% port)

def setNtpConf(port = '', ip = ''):
    adr = ''
    pps = ''
    if port:
        pps = adr = '127.127.20.%s' % port
    if ip:
        adr = ip + ' ' + adr if adr else ip

    # /etc/conf.d/ntp-client 
    #config = ConfigObj(NTP_CLIENT_PATH, list_values = False)
    #config['NTPCLIENT_OPTS'] = '"-p -s %s"' % adr
    #config.write()
    with open(NTP_CLIENT_PATH, 'w') as f:
        f.write('NTPCLIENT_OPTS="-p -s %s"' % adr)

    # /etc/ntp.conf
    # Удалить fudge и server строки 
    call(['sed', '-i', '-e', '/^fudge/ d',
        '-e', '/^server/ d', NTP_CONF_PATH])

    if not port and not ip:
        return

    with open(NTP_CONF_PATH, 'a+') as f:
        if port:
            f.write('server %s minpoll 4 maxpoll 4 prefer\n' % pps)
            f.write('fudge %s flag1 1 flag3 1\n' % pps)
        if ip:
            f.write('server %s\n' % ip)

def setConfNtpd():
    # Тупо сбросить параметр NTPD_OPTS
    config = ConfigObj(NTPD_PATH, list_values = False)
    config['NTPD_OPTS'] = '""'
    config.write()

class Time:
    def __init__(self):
        pass

    def GET(self):
        nocache()


        tzFrm = tzForm()
        tzFrm['tz'].set_value(curZone())

        modeFrms = modeForms
        smode = sync_mode()
        for f in modeFrms:
            f[''].set_value(smode)
       
        ctime = localtime()
        timeForm['year'].args = [''] + years(ctime.tm_year)
        timeFrm = timeForm()
        if smode == 'manually':
            timeFrm['day'].set_value(str(ctime.tm_mday))
            timeFrm['month'].set_value(MONTHS[ctime.tm_mon-1])
            timeFrm['year'].set_value(str(ctime.tm_year))
            timeFrm['hour'].set_value(str(ctime.tm_hour))
            timeFrm['minute'].set_value(str(ctime.tm_min))

        gpsFrm = gpsForm()
        ports = comPorts()
        pp = [COM_PORTS[0],]
        for i in ports:
            pp.append(COM_PORTS[i])
        gpsFrm['port'].args = pp
        gpsForm['port'].args = pp
        if smode == 'gps':
            cur_port = curPort()
            gpsFrm['port'].set_value(COM_PORTS[cur_port])

        ntpFrm = ntpForm()
        if smode == 'ntp':
            ntpFrm['server_address'].set_value(serverAddress())

        return render.dotime(tzFrm, modeFrms, timeFrm, gpsFrm, ntpFrm, title = title)

    def POST(self):
        '''
        Проверяются только данные выбранного режима синхронизации.
        Остальные данные записываются в файлы как есть
        '''
        valid = True

        tzFrm = tzForm()
        modeFrm = modeForm()
        timeFrm = timeForm()
        gpsFrm = gpsForm()
        ntpFrm = ntpForm()
        
        tzFrm.validates()
        modeFrm.validates()
        timeValid = timeFrm.validates()
        gpsFrm.validates()
        ntpFrm.validates()
        
        mode = modeFrm[''].get_value()

        if mode == 'manually':
            if timeValid:
                year = int(timeFrm['year'].get_value())
                month = MONTHS.index(timeFrm['month'].get_value())
                day = int(timeFrm['day'].get_value())
                hour = int(timeFrm['hour'].get_value())
                minute = int(timeFrm['minute'].get_value())
            if not timeValid or not dateValid(year, month, day):
                valid = False 
                timeFrm.note = NOTE_INVALID_VALUE

        server_address = ntpFrm['server_address'].get_value()
        if mode == 'ntp' and not addressValid(server_address):
            valid = False 
            ntpFrm['server_address'].note = NOTE_INVALID_VALUE

        port = COM_PORTS.index(gpsFrm['port'].get_value())
        if mode == 'gps' and port == 0:
            valid = False
            gpsFrm['port'].note = NOTE_INVALID_VALUE
        
        if not valid:
            modeFrms = modeForms
            for i in xrange(len(modeFrms)):
                modeFrms[i][''].set_value(mode)
            if mode != 'manually':
                timeFrm.note = ''
            return render.dotime(tzFrm, modeFrms, timeFrm, gpsFrm, ntpFrm, title = title)

        # Файлы конфигурации
        tz = tzFrm['tz'].get_value()
        if curZone() != tz:
            setTimezone(tz)

        setConfNtpd()

        if mode == 'gps':
            if port != curPort():
                setPort(port - 1)

            setNtpConf(port=str(port - 1))
        
        elif mode == 'ntp':
            setNtpConf(ip=ntpFrm['server_address'].get_value())
        else:
            setNtpConf()

        # Сервисы
        oldmode = sync_mode()
        if mode == 'manually':
            if oldmode != 'manually':
                del_service('ntpd')
                del_service('ntp-client')
                if oldmode == 'gps':
                    del_service('ntp-pps')
            
            if not DEBUG_PATH:
                setDatetime(int(year), int(month), int(day), int(hour), int(minute))
        
        else:
            if mode == 'gps':
                add_service('ntp-pps')
            
            # быстрая(грубая) установка
            del_service('ntp-client')

            add_service('ntp-client')
            add_service('ntpd')

        return render.completion(title)
