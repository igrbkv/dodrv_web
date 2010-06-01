# -*- coding: utf-8 -*-

import web
from config import render

class Index:
    title = 'Состояние'
    def GET(self):
        web.header('Content-Type', 'text/html; charset= utf-8')
        return render.index(self.title, 'Igor')
