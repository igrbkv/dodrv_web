# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, rewriteConfigXml
from utils import restart_service
from formatting import getFirstDev

def createDiscretesForm(dev):
    cb = (form.Checkbox('d%s' % i, value = i,
        checked = xml['device'][dev]['discrete'][str(i)]['in_use'] == 'yes')
            for i in xrange(int(xml['device'][dev]['discretes'])))
    df = form.Form(*cb)
    return df

title = 'Дискреты'


class Discretes:

    def GET(self, dev=''):
        web.header('Content-Type', 'text/html; charset= utf-8')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        web.header('Pragma', 'no-cache')

        if not dev:
            dev = getFirstDev()
            if not dev:
                return render.emptypage(title = title)

        df = createDiscretesForm(dev)
        df.dev = dev

        return render.discretes(df, title = title)

    def POST(self, dev=''):
        df = createDiscretesForm(dev)
        df.validates()
        for cb in df.inputs:
            inUse = 'no'
            if cb.get_value():
                inUse = 'yes'
            xml['device'][dev]['discrete'][str(cb.value)]['in_use'] = inUse

        rewriteConfigXml()
        restart_service('dofilters.pov%s' % str(dev))

        return render.completion(title)
