# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender, rewriteConfigXml
from utils import restartFilters
from formatting import getFirstDev

def createAnalogsForm(dev):
    cb = (form.Checkbox('a%s' % i, value = i, checked = xml['device'][dev]['analog'][str(i)]['in_use'] == 'yes')
            for i in xrange(int(xml['device'][dev]['analogs'])))
    af = form.Form(*cb)
    return af

title = 'Аналоги'

class Analogs:

    def GET(self, dev=''):
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')
        
        if not dev:
            dev = getFirstDev()
            if not dev:
                return render.emptypage(title = title)

        af = createAnalogsForm(dev)
        af.dev = dev
        return render.analogs(af, title = title)

    def POST(self, dev=''):
        af = createAnalogsForm(dev)
        af.validates()
        for cb in af.inputs:
            inUse = 'no'
            if cb.get_value():
                inUse = 'yes' 
            xml['device'][dev]['analog'][str(cb.value)]['in_use'] = inUse
        
        rewriteConfigXml()
        restartFilters(dev)
        return render.completion(title)
