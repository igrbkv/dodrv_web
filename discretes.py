# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender

def createDiscretesForm(dev):
    cb = (form.Checkbox('d%s' % i, value = i, 
        data = xml['device'][dev]['discrete'][str(i)], 
        checked = xml['device'][dev]['discrete'][str(i)]['in_use'] == 'yes')
            for i in xrange(int(xml['device'][dev]['discretes'])))
    df = form.Form(*cb)
    return df

class Discretes:
    title = 'Дискреты'

    def GET(self, dev):
        web.header('Cache-Control', 'no-cache, must-revalidate')        
        df = createDiscretesForm(dev)
        df.devs = len(xml['device']) 
        df.dev = dev
            
        #print xmlRender(xml)
        return render.discretes(df, title = self.title)

    def POST(self, dev):
        df = createDiscretesForm(dev)
        df.validates()
        for cb in df.inputs:
            inUse = 'no'
            if cb.get_value():
                inUse = 'yes' 
            print cb.data['id'], inUse
            xml['device'][dev]['discrete'][cb.data['id']]['in_use'] = inUse
        
        #print xmlRender(xml)
        return render.completion(self.title)
