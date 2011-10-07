# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender, rewriteConfigXml
from utils import restartFilters

def createAnalogsForm(dev):
    cb = (form.Checkbox('a%s' % i, value = i, data = xml['device'][dev]['analog'][str(i)], checked = xml['device'][dev]['analog'][str(i)]['in_use'] == 'yes')
            for i in xrange(int(xml['device'][dev]['analogs'])))
    af = form.Form(*cb)
    return af

title = 'Аналоги'

class PreAnalogs:
    def GET(self):
        for i in xrange(len(xml['device'])):
            if xml['device'][str(i)]["exists"]:
                raise web.seeother('/config/analogs/%s' % i)
        return render.emptypage(title = title)

class Analogs:

    def GET(self, dev):
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')

        af = createAnalogsForm(dev)
        af.devs = (i for i in xrange(len(xml['device'])) 
            if xml['device'][str(i)]['exists']) 
        af.dev = dev
        return render.analogs(af, title = title)

    def POST(self, dev):
        af = createAnalogsForm(dev)
        af.validates()
        for cb in af.inputs:
            inUse = 'no'
            if cb.get_value():
                inUse = 'yes' 
            xml['device'][dev]['analog'][cb.data['id']]['in_use'] = inUse
        
        rewriteConfigXml()
        restartFilters(dev)
        return render.completion(title)
