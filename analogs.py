# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender

def createAnalogsForm(dev):
    cb = (form.Checkbox('a%s' % i, value = i, data = xml['device'][dev]['analog'][str(i)], checked = xml['device'][dev]['analog'][str(i)]['in_use'] == 'yes')
            for i in xrange(int(xml['device'][dev]['analogs'])))
    af = form.Form(*cb)
    return af

class Analogs:
    title = 'Аналоги'

    def GET(self, dev):
        web.header('Cache-Control', 'no-cache, must-revalidate')        
        af = createAnalogsForm(dev)
        af.devs = len(xml['device']) 
        af.dev = dev
            
        return render.analogs(af, title = self.title)

    def POST(self, dev):
        af = createAnalogsForm(dev)
        af.validates()
        for cb in af.inputs:
            inUse = 'no'
            if cb.get_value():
                inUse = 'yes' 
            xml['device'][dev]['analog'][cb.data['id']]['in_use'] = inUse
        
        print xmlRender(xml)
        return render.completion(self.title)
