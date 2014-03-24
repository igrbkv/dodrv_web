# -*- coding: utf-8 -*-
'''
1. Форма
Доставка файлов.

Почта
Адрес SMTP-сервера:
[] Использовать SSL/TLS
Аккаунт:
Пароль:
Телефон:
Расписание:
                 
Удл.    Адрес                    Файлы
    получателя  Пуски События Самописцы Журнал     

FTP-сервер
Удл. Адрес Логин Пуски События Самописцы Журнал Телефон Расписание
Задание адреса удаленного ftp-сервера не
обязательно, будет подставлен адрес удаленного клиента, назначенный PPP.
Адрес также может быть задан в символьном виде.


[Применить]

2. Файлы конфигурации

/etc/ssmtp/revaliases:
root:<account>  # igor@parma.spb.ru

/etc/ssmtp/ssmtp.conf:
mailhub=<ip-address>[:<port>]
AuthUser=<account>  # igor@parma.spb.ru
AuthPass=<psw>
UseTLS=YES|NO
phone=1234567
schedule=13-14 18-7

/etc/dodrv/smtpdelivery:
<address>;{E|I|R|L|Z}
...

/etc/dodrv/ftpdelivery:
<ftp-address>;<login>;<psw>;{E|I|R|L};<phone>;<schedule>
...

/etc/dodrv/recorderdelivery:
<address>;{E|I|R|L}
...

3. Передача на другой регистратор осуществляется по ftp.
4. Расписание - только время в формате [Н1-К1 [H2-K2]...[НN-КN]],
где Н-начало периода в часах, К-конец периода, например:
12-13 18-7
5. Формат ftp-адреса:
[ftp://][<ip_or_address_or_empty>][:port][/<dir1>...[/<dirN>]]
в доставке соответственно:
/dodrv/delivery/ftp/[<ip_or_address_or_empty>][:port][ <dir1>]...[ dirN] [phone],
например:
ftp://ftp.parma.spb.ru:21/recorders/r1 =>
/dodrv/delivery/ftp/ftp.parma.spb.ru:21 recorders r1
и <ftp-address> в /etc/dodrv/ftpdelivery = ftp.parma.spb.ru:21/recorders/r1
MAX FILE NAME IN EXT4 = 255
6. FIXME Добавить "сжимать файлы", добавляя тип файла 'Z'
'''
from web import form
from config import render, DEBUG_PATH
from http import nocache
from configobj import ConfigObj
from re import sub
from utils import restart_service
from subprocess import call

SSMTPCONF_PATH = DEBUG_PATH + '/etc/ssmtp/ssmtp.conf'
REVALIASES_PATH = DEBUG_PATH + '/etc/ssmtp/revaliases'
SMTPDELIVERY_PATH = DEBUG_PATH + '/etc/dodrv/smtpdelivery'
FTPDELIVERY_PATH = DEBUG_PATH + '/etc/dodrv/ftpdelivery'
RECORDERDELIVERY_PATH = DEBUG_PATH + '/etc/dodrv/recorderdelivery'
MAX_DELIVERYS = 10
# FIXME 
# 1. Проверка адресов
# 2. Проверка расписания
MAIL_REGEXP = '^[0-9a-zA-Z_.,@-]*$'
FTP_REGEXP = '^[0-9a-zA-Z_.-:/]*$'
SCHEDULE_REGEXP = '^[0-9 -]*$'
PHONE_REGEXP = '^[TP]?[0-9#*-]*$'

NOT_FILLED_NOTE = '* Не заполнено'
NO_FILES_NOTE = '* Не заданы файлы'
NO_ADDRESS_NOTE = '* Не задан адрес'
NOT_VALID = '* Неверное значение'
ADDRESS_EXISTS_NOTE = '* Дублирование адреса'

def scheduleValid(sched):
    tt=sched.split()
    try:
        for t in tt:
            b, e = t.split('-')
            l = [str(i) for i in xrange(24)]
            if b == e or b not in l or e not in l:
                return False
    except:
        return False
    return True 


def createMailForm(idx, args):
    mf = form.Form(
        form.Checkbox(idx + '_mail_del', value = 'value', checked = False),
        form.Textbox(idx + '_mail_adr', value = args[0], readonly = 'on'),
        form.Checkbox(idx + '_mail_emg', value = 'value', 
            checked = 'E' in args[1]),
        form.Checkbox(idx + '_mail_inf', value = 'value', 
            checked = 'I' in args[1]),
        form.Checkbox(idx + '_mail_rec', value = 'value', 
            checked = 'R' in args[1]),
        form.Checkbox(idx + '_mail_log', value = 'value', 
            checked = 'L' in args[1]))
    return mf

def createFtpForm(idx, args):
    ff = form.Form(
        form.Checkbox(idx + '_ftp_del', value = 'value', checked = False),
        form.Textbox(idx + '_ftp_adr', value = args[0], READONLY = 'ON'),
        form.Textbox(idx + '_ftp_login',
            form.Validator('* Длина логина не должна превышать 20 символов', 
            lambda i: len(i) <= 20 ), value = args[1]),
        form.Textbox(idx + '_ftp_psw',
            form.Validator('* Длина пароля не должна превышать 20 символов', 
            lambda i: len(i) <= 20 ), value = args[2]),
        form.Checkbox(idx + '_ftp_emg', value = 'value', 
            checked = 'E' in args[3]),
        form.Checkbox(idx + '_ftp_inf', value = 'value', 
            checked = 'I' in args[3]),
        form.Checkbox(idx + '_ftp_rec', value = 'value', 
            checked = 'R' in args[3]),
        form.Checkbox(idx + '_ftp_log', value = 'value', 
            checked = 'L' in args[3]),
        form.Textbox(idx + '_ftp_phone',
            form.Validator('* Длина номера не должна превышать 20 символов', 
                lambda i: len(i) <= 20 ), value = args[4], READONLY = 'ON'), 
        form.Textbox(idx + '_ftp_sched',
            form.Validator('* Длина расписания не должна превышать 20 символов',
            lambda i: len(i) <= 40),
            form.regexp(SCHEDULE_REGEXP, '* Недопустимые символы в расписании'),
            form.Validator(NOT_VALID, lambda i: scheduleValid(i)),
            value = args[5]))
    return ff

def createRecorderForm(idx, args):
    rf = form.Form(
        form.Checkbox(idx + '_recorder_del', value = 'value', checked = False),
        form.Textbox(idx + '_recorder_adr', value = args[0], readonly = 'on'),
        form.Checkbox(idx + '_recorder_emg', value = 'value', 
            checked = 'E' in args[1]),
        form.Checkbox(idx + '_recorder_inf', value = 'value', 
            checked = 'I' in args[1]),
        form.Checkbox(idx + '_recorder_rec', value = 'value', 
            checked = 'R' in args[1]),
        form.Checkbox(idx + '_recorder_log', value = 'value', 
            checked = 'L' in args[1]))
    return rf


def readMails():
    d = [] 
    try:
        with open(SMTPDELIVERY_PATH, 'r') as f:
            lst = f.readlines()
        idx = 0
        for l in lst:
            l = l.strip().split(';')
            d.append(createMailForm(str(idx), l))
            idx += 1
            
    except:
        pass
    return d

def readFtps():
    d = []
    try:
        with open(FTPDELIVERY_PATH, 'r') as f:
            lst = f.readlines()
        idx = 0
        for l in lst:
            l = l.strip().split(';')
            d.append(createFtpForm(str(idx), l))
            idx += 1
                
    except:
        pass
    return d

def readRecorders():
    d = []
    try:
        with open(RECORDERDELIVERY_PATH, 'r') as f:
            lst = f.readlines()
        idx = 0
        for l in lst:
            l = l.strip().split(';')
            d.append(createRecorderForm(str(idx), l))
            idx += 1
                
    except:
        pass
    return d

smtpForm = form.Form(
    form.Textbox('mailhub',
        form.Validator('* Длина адреса не должна превышать 40 символов', 
            lambda i: len(i) <= 40 ), description = 'SMTP-сервер[:порт]'),
    form.Checkbox('UseTLS', value = 'value', checked = False, 
        description = 'Использовать SSL/TLS'),
    form.Textbox('AuthUser',
        form.Validator('* Длина адреса не должна превышать 40 символов', 
            lambda i: len(i) <= 40 ), description = 'Аккаунт'),
    form.Textbox('AuthPass',
        form.Validator('* Длина пароля не должна превышать 20 символов', 
            lambda i: len(i) <= 20 ), description = 'Пароль'),
    form.Textbox('phone',
        form.Validator('* Длина номера не должна превышать 20 символов', 
            lambda i: len(i) <= 20 ), 
        form.regexp(PHONE_REGEXP, '* Недопустимые символы'),
        description = 'Телефон'),
    form.Textbox('schedule', 
        form.Validator('* Длина расписания не должна превышать 20 символов',
        lambda i: len(i) <= 20),
        form.regexp(SCHEDULE_REGEXP, '* Недопустимые символы в расписании'),
        form.Validator(NOT_VALID, lambda i: scheduleValid(i)),
        description = 'Расписание'))

def readSmtp():
    smtpFrm = smtpForm()
    ssmtpconf = ConfigObj(SSMTPCONF_PATH)
    
    try:
        with open(SMTPDELIVERY_PATH, 'r') as f:
            l = f.readline().strip().split(';')
        names = ('mailhub', 'UseTLS', 'AuthUser', 'AuthPass', 'phone', 
                'schedule')
        for i in xrange(len(names)):
            val = ssmtpconf[names[i]]
            if names[i] != 'UseTLS':
                smtpFrm[names[i]].set_value(val)
            else:
                smtpFrm[names[i]].set_value(val == 'YES')
    except:
        pass

    return smtpFrm


newMailForm = form.Form(
    form.Textbox('new_mail_adr',
        form.Validator('* Длина адреса не должна превышать 40 символов', 
            lambda i: len(i) <= 40 ),
        form.regexp(MAIL_REGEXP, '* Недопустимые символы в адресе')),
        form.Checkbox('new_mail_emg', value = 'value', checked = False),
        form.Checkbox('new_mail_inf', value = 'value', checked = False),
        form.Checkbox('new_mail_rec', value = 'value', checked = False),
        form.Checkbox('new_mail_log', value = 'value', checked = False))

newFtpForm = form.Form(
    form.Textbox('new_ftp_adr',
        form.Validator('* Длина адреса не должна превышать 80 символов', 
        lambda i: len(i) <= 80 ),
        form.regexp(FTP_REGEXP, '* Недопустимые символы в адресе')),
    form.Textbox('new_ftp_login',
        form.Validator('* Длина логина не должна превышать 20 символов', 
        lambda i: len(i) <= 20 )),
    form.Textbox('new_ftp_psw',
        form.Validator('* Длина пароля не должна превышать 20 символов', 
        lambda i: len(i) <= 20 )),
    form.Checkbox('new_ftp_emg', value = 'value', checked = False),
    form.Checkbox('new_ftp_inf', value = 'value', checked = False),
    form.Checkbox('new_ftp_rec', value = 'value', checked = False),
    form.Checkbox('new_ftp_log', value = 'value', checked = False),
    form.Textbox('new_ftp_phone',
        form.Validator('* Длина номера не должна превышать 20 символов', 
        lambda i: len(i) <= 20 )),
    form.Textbox('new_ftp_sched',
        form.Validator('* Длина расписания не должна превышать 20 символов', 
        lambda i: len(i) <= 20 ),
        form.regexp(SCHEDULE_REGEXP, '* Недопустимые символы в расписании')))

newRecorderForm = form.Form(
    form.Textbox('new_recorder_adr',
        form.Validator('* Длина адреса не должна превышать 40 символов', 
            lambda i: len(i) <= 40 ),
        form.regexp(MAIL_REGEXP, '* Недопустимые символы в адресе')),
        form.Checkbox('new_recorder_emg', value = 'value', checked = False),
        form.Checkbox('new_recorder_inf', value = 'value', checked = False),
        form.Checkbox('new_recorder_rec', value = 'value', checked = False),
        form.Checkbox('new_recorder_log', value = 'value', checked = False))

def getTypes(f, n):
    types = ''
    if f[n + '_emg'].get_value():
        types += 'E'
    if f[n + '_inf'].get_value():
        types += 'I'
    if f[n + '_rec'].get_value():
        types += 'R'
    if f[n + '_log'].get_value():
        types += 'L'
    return types




class Delivery:
    title = 'Доставка файлов'

    def GET(self):
        nocache()
        
        smtpFrm = readSmtp()

        mailFrms = readMails()
        newMailFrm = newMailForm() if len(mailFrms) <= MAX_DELIVERYS else None

        ftpFrms = readFtps()
        newFtpFrm = newFtpForm() if len(ftpFrms) <= MAX_DELIVERYS else None
        
        recFrms = readRecorders()
        newRecFrm = newRecorderForm() if len(recFrms) <= MAX_DELIVERYS else None

        return render.delivery(smtpFrm, mailFrms, newMailFrm, ftpFrms, 
                newFtpFrm, recFrms, newRecFrm, self.title)

    def POST(self):
        valid = True

        smtpFrm = readSmtp()

        smtpFrm.validates()
        valid &= smtpFrm.valid

        smtpFilled = smtpFrm['mailhub'].get_value().strip() and\
            smtpFrm['AuthUser'].get_value().strip()

        mailFrms = readMails()
        for i in xrange(len(mailFrms)):
            mailFrms[i].validates()
            si = str(i)
            if not mailFrms[i][si + '_mail_del'].get_value():
                if not getTypes(mailFrms[i], si + '_mail'):
                    valid = False
                    mailFrms[i][si + '_mail_adr'].note = NO_FILES_NOTE
                else:
                    valid &= mailFrms[i].valid

        
        newMailFrm = newMailForm() if len(mailFrms) <= MAX_DELIVERYS else None
        newMailAdr = ''
        if newMailFrm:
            newMailFrm.validates()
            newMailAdr = newMailFrm['new_mail_adr'].get_value().strip()
            types = getTypes(newMailFrm, 'new_mail')
            if newMailAdr:
                if not types:
                    valid = False
                    newMailFrm['new_mail_adr'].note = NO_FILES_NOTE
                else:
                    valid &= newMailFrm.valid
            elif types:
                valid = False
                newMailFrm['new_mail_adr'].note = NO_ADDRESS_NOTE

        # Smtp-параметры д.б. заполнены, если есть доставки 
        if not smtpFilled and (len(mailFrms) or newMailAdr):
            for n in ('mailhub', 'AuthUser'):
                smtpFrm[n].note = NOT_FILLED_NOTE
            valid = False
        #sched = smtpFrm['schedule']
        #if sched and not sheduleValid(sched):
        #    smtpFrm['schedule'].note = NOT_VALID
        #    valid = False

        ftpFrms = readFtps()
        for i in xrange(len(ftpFrms)):
            si = str(i)
            ftpFrms[i].validates()
            if not ftpFrms[i][si + '_ftp_del'].get_value():
                if not getTypes(ftpFrms[i], si + '_ftp'):
                    valid = False
                    ftpFrms[i][si + '_ftp_adr'].note = NO_FILES_NOTE
                else:
                    valid &= ftpFrms[i].valid

        newFtpFrm = newFtpForm() if len(ftpFrms) <= MAX_DELIVERYS else None
        if newFtpFrm:
            newFtpFrm.validates()
            types = getTypes(newFtpFrm, 'new_ftp')
            # обрезать "ftp://" если есть
            newFtpAdr = sub('ftp://', '', newFtpFrm['new_ftp_adr'].get_value())
            if newFtpAdr or newFtpFrm['new_ftp_phone'].get_value():
                if not types:
                    valid = False
                    newFtpFrm['new_ftp_adr'].note = NO_FILES_NOTE
                else:
                    # проверка дублирования
                    new_adr = newFtpFrm['new_ftp_adr'].get_value()
                    new_phone = newFtpFrm['new_ftp_phone'].get_value()
                    for i in xrange(len(ftpFrms)):
                        si = str(i)
                        if ftpFrms[i][si + '_ftp_del'].get_value():
                            continue
                        adr = ftpFrms[i][si+ '_ftp_adr'].get_value()
                        phone = ftpFrms[i][si + '_ftp_phone'].get_value()
                        if adr == new_adr and phone == new_phone:
                            valid = False
                            newFtpFrm['new_ftp_adr'].note = ADDRESS_EXISTS_NOTE
                            break

                    valid &= newFtpFrm.valid

            elif types or newFtpFrm['new_ftp_sched'].get_value():
                valid = False
                newFtpFrm['new_ftp_adr'].note = NO_ADDRESS_NOTE

        recFrms = readRecorders()
        for i in xrange(len(recFrms)):
            recFrms[i].validates()
            si = str(i)
            if not recFrms[i][si + '_recorder_del'].get_value():
                if not getTypes(recFrms[i], si + '_recorder'):
                    valid = False
                    recFrms[i][si + '_recorder_adr'].note = NO_FILES_NOTE
                else:
                    valid &= recFrms[i].valid


        newRecFrm = newRecorderForm() if len(recFrms) <= MAX_DELIVERYS else None
        if newRecFrm:
            newRecFrm.validates()
            types = getTypes(newRecFrm, 'new_recorder')
            if newRecFrm['new_recorder_adr'].get_value():
                if not types:
                    valid = False
                    newRecFrm['new_recorder_adr'].note = NO_FILES_NOTE
                else:
                    valid &= newRecFrm.valid
            elif types:
                valid = False
                newRecFrm['new_recorder_adr'].note = NO_ADDRESS_NOTE


        if not valid:
            return render.delivery(smtpFrm, mailFrms, newMailFrm, ftpFrms, 
                newFtpFrm, recFrms, newRecFrm, self.title)
        
        # запись изменений
        # в SSMTPCONF_PATH & REVALIASES_PATH
        with open(SSMTPCONF_PATH, 'w+') as ssmtp:
            for n in ('mailhub', 'UseTLS', 'AuthUser', 'AuthPass', 'phone',
                    'schedule'):
                v = smtpFrm[n].get_value()
                if n == 'UseTLS':
                    v = 'YES' if v else 'NO'
                elif n == 'AuthUser':
                    with open(REVALIASES_PATH, 'w+') as rev:
                        rev.write('root:%s\n' % v)
                ssmtp.write('%s=%s\n' % (n, v))

        # в SMTPDELIVERY_PATH
        with open(SMTPDELIVERY_PATH, 'w+') as conf:
            smtp = ''
            for i in xrange(len(mailFrms)):
                si = str(i)
                if mailFrms[i][si + '_mail_del'].get_value():
                    continue
                types = getTypes(mailFrms[i], si + '_mail')
                conf.write('%s%s;%s\n' % \
                    (smtp, mailFrms[i][si + '_mail_adr'].get_value(), types))

            if newMailFrm:
                adr = newMailFrm['new_mail_adr'].get_value()
                if adr:
                    types = getTypes(newMailFrm, 'new_mail')
                    conf.write('%s%s;%s\n' % (smtp, adr, types))

        # в FTPDELIVERY_PATH
        with open(FTPDELIVERY_PATH, 'w+') as conf:
            for i in xrange(len(ftpFrms)):
                si = str(i)
                if ftpFrms[i][si + '_ftp_del'].get_value():
                    continue
                adr = ftpFrms[i][si+ '_ftp_adr'].get_value()
                login = ftpFrms[i][si+ '_ftp_login'].get_value()
                psw = ftpFrms[i][si + '_ftp_psw'].get_value()
                phone = ftpFrms[i][si + '_ftp_phone'].get_value()
                types = getTypes(ftpFrms[i], si + '_ftp')
                sched = ftpFrms[i][si + '_ftp_sched'].get_value()
                conf.write('%s;%s;%s;%s;%s;%s\n' %\
                    (adr, login, psw, types, phone, sched))

            if newFtpFrm:
                phone = newFtpFrm['new_ftp_phone'].get_value()
                if newFtpAdr or phone:
                    login = newFtpFrm['new_ftp_login'].get_value()
                    psw = newFtpFrm['new_ftp_psw'].get_value()
                    types = getTypes(newFtpFrm, 'new_ftp')
                    sched = newFtpFrm['new_ftp_sched'].get_value()
                    conf.write('%s;%s;%s;%s;%s;%s\n' %\
                        (newFtpAdr, login, psw, types, phone, sched))

        # в RECORDERDELIVERY_PATH
        with open(RECORDERDELIVERY_PATH, 'w+') as conf:
            for i in xrange(len(recFrms)):
                si = str(i)
                if recFrms[i][si + '_recorder_del'].get_value():
                    continue
                adr = recFrms[i][si + '_recorder_adr'].get_value()
                types = getTypes(recFrms[i], si + '_recorder')
                conf.write('%s;%s\n' % (adr, types))

            if newRecFrm:
                adr = newRecFrm['new_recorder_adr'].get_value()
                if adr:
                    types = getTypes(newRecFrm, 'new_recorder')
                    conf.write('%s;%s\n' % (adr, types))

        # Перезапустить сервис отслеживания файлов регистрации/самописца 
        restart_service('dlinkd')

        return render.completion(self.title)
