# -*- coding: utf-8 -*-


import config
import menu

"""
class ctx():
    path = '/log'

class web:
    ctx=ctx()

web = web()
"""

def recorderName():
    name = config.xml['name']
    if name:
        return name
    else:
        return 'Регистратор %s' % config.xml['id']

def isCurPath(path):
    return config.web.ctx.path.split('/')[1] == path.split('/')[1]

def getMenu():
    if config.web.ctx.path == '/login': 
        return menu.loginMenu
    return menu.mainMenu 

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
    devs = (str(i) for i in xrange(len(config.xml['device'])) 
        if config.xml['device'][str(i)]['exists']) 
    return devs

def getFirstDev():
    for i in xrange(len(config.xml['device'])):
        if config.xml['device'][str(i)]["exists"]:
            return str(i)
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

    l = [i for i in xrange(page-config.PAGES_AROUND, page+config.PAGES_AROUND+1) if i > 0 and i <= pages]

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

def recFileName(rec, pov, start, end, ext):
    return rec + '_' + pov + '_' + start[:6] + '(' + start[6:] + '-' +\
            end[6:] + ')' + ext
"""
if __name__ == '__main__':
    print getMenu()
"""
