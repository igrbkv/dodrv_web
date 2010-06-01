# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, xmlRender

class Discretes:
    title = 'Дискреты'


    def GET(self, channel):
        df = form.Form()
        df.channels = len(xml['device']) 
        df.channel = channel
        df.inputs = (        
            form.Checkbox('d%s' % i, value = xml['device'][channel]['discrete']['in_use'] == 'yes', description = '')
                for i in xrange(int(xml['device'][channel]['discretes'])))
            
        return render.discretes(df, title = self.title)

    def POST(self, channel):
        return render.completion(self.title, 'Данные записаны')
