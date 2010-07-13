# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender

class Discretes:
    title = 'Дискреты'


    def GET(self, channel):
        web.header('Cache-Control', 'no-cache, must-revalidate')        
        df = form.Form()
        df.channels = len(xml['device']) 
        df.channel = channel
        df.inputs = (        
            form.Checkbox('d%s' % i, value = xml['device'][channel]['discrete'][str(i)], checked = xml['device'][channel]['discrete'][str(i)]['in_use'] == 'yes', description = '')
                for i in xrange(int(xml['device'][channel]['discretes'])))
            
        return render.discretes(df, title = self.title)

    def POST(self, channel):
        df = form.Form()
        df.validates()
        for cb in df.inputs:
            inUse = 'no'
            if cb.get_value():
                inUse = 'yes' 
            xml['device'][channel]['discrete'][cb.value['id']]['in_use'] = inUse
        
        print xmlRender(xml)
        return render.completion(self.title, 'Данные записаны')
