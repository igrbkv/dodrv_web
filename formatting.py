# -*- coding: utf-8 -*-


import config
import menu
import session
from utils import recorderMode

"""
class ctx():
    path = '/log'

class web:
    ctx=ctx()

web = web()
"""

def recorderName():
    return u'Регистратор ' + config.xml['id']

def userName():
    return session.getUser()

def recMode():
    mode_names = (
        u'Работа',
        u'Поверка',
        u'Тесты',
        u'Настройка',
        u'Останов',
        u'Выключение',
        u'Ав. останов')
    if config.DEBUG_PATH:
        return mode_names[0]
    rm = recorderMode()
    if rm == -1:
        return u'Ошибка'
    return mode_names[rm]


def isCurPath(path):
    return config.web.ctx.path.split('/')[1] == path.split('/')[1]

def getMenu():
    if config.web.ctx.path == '/login':
        return menu.loginMenu
    if session.getUser() == 'admin':
        return menu.mainMenu
    else:
        return menu.userMenu

def attrs(d):
    s = ''
    for k, v in d.iteritems():
        if isinstance(v, basestring):
            s += '%s="%s" ' % (k, v)
    return s.strip()

def getAnalog(dev, i):
    return config.xml['device'][dev]['analog'][str(i)]

def getDiscrete(dev, i):
    return config.xml['device'][dev]['discrete'][str(i)]

def getDevs():
    devs = (str(i) for i in xrange(config.MAX_POV)
        if config.xml['device'].has_key(str(i)) and
            config.xml['device'][str(i)]['exists'] and
            config.xml['device'][str(i)]['in_use'] == 'yes')
    return devs

def getFirstDev():
    for i in xrange(config.MAX_POV):
        ii = str(i)
        if config.xml['device'].has_key(ii) and \
                config.xml['device'][ii]["exists"] and \
                config.xml['device'][ii]['in_use'] == 'yes':
            return ii
    return ''

def getPages(page, pages):
    '''
    Из номера текущей страницы и общего числа страниц сформировать
    список страниц-ссылок.
    Например для page=5, pages=10, PAGES_AROUND=2:
    ['1', '...', '3','4','5','6', '7', '...', '10']

    '''
    lst = []
    if not pages:
        return lst

    l = [i for i in xrange(page-config.PAGES_AROUND,
        page+config.PAGES_AROUND+1) if i > 0 and i <= pages]

    if l[0] != 1:
        lst.append('1')
    if l[0]-1 > 1:
        lst.append('...')
    lst += map(str, l)
    if l[-1]+1 < pages:
        lst.append('...')
    if l[-1] != pages:
        lst.append(str(pages))
    return lst

def fmtDate(date):
    '''
    Преобразование yymmddhhmmss<ms> к виду
    dd/mm/yy hh:mm:ss.ms
    '''

    d = date[4:6] + '/' +date[2:4] + '/' + date[:2] + ' '\
        + date[6:8] + ':' + date[8:10] + ':' + date[10:12]
    if len(date) == 15:
        d += '.' + date[12:15]
    return d

def filesInPage():
    return config.FILES_IN_PAGE

def disableElement(elm, strn):
    ss = strn.split()
    for i in xrange(len(ss)):
        if elm in ss[i]:
            ss.insert(i+1, 'disabled')
            break;
    return ' '.join(ss)


"""
if __name__ == '__main__':
    print getMenu()
"""
