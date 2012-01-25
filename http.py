# -*- coding: utf-8 -*-
import web

def nocache():
    web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
    web.header('Cache-Control', 'post-check=0, pre-check=0', False)
    web.header('Pragma', 'no-cache')
