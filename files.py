# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, EMERGENCY_PATH, RECORDER_PATH, FILES_IN_PAGE
from http import nocache
from os import listdir, path

COMTRADE_EXTENTIONS=['.CFG','.DAT', '.INFO', '.OMP']

class Emergencys:
    title = 'Файлы аварий'

    def GET(self, page='1'):
        '''
        Считывает все файлы из папки EMERGENCY_PATH
        <recorder id>_<pov id>_yymmddhhmmss<ms>.[CFG|DAT|INFO|OMP]
        Сортирует по времени и формирует список файлов текущей страницы 
        (размера не более FILES_IN_PAGE) след. вида:
        [
         [<recorder_id>,<pov_id>, <yymmddhhmmss<ms>>, [<расширение1>, <расширение2>...]],
         [...]
        ]
        Например:
        [
         ['1', '0', '120119190000100', ['.CFG', '.DAT', '.INFO'])
        ]

        '''
        page = int(page)

        nocache()

        entries = sorted(map(path.splitext, listdir(EMERGENCY_PATH)))
        cn = None
        files = []
        print entries
        for n, e in entries:
            if cn != n:
                cn = n
                try:
                    rec, pov, time = n.split('_')
                except:
                    # неверный формат имени файла
                    continue
                files.append([rec, pov, time, [e,]])
            else:
                files[-1][3].append(e)
        del entries
        pages= len(files)/FILES_IN_PAGE+1
        files.sort(key = lambda f: f[2])
        # выбор файлов текущей страницы
        files = files[(page-1)*FILES_IN_PAGE: min(len(files), page*FILES_IN_PAGE-1)] 
        return render.emgfiles(page, pages, files, title = self.title)

class Recorders:
    title = 'Файлы самописца'

    def GET(self, page='1'):
        '''
        Считывает все файлы из папки RECORDER_PATH
        <recorder id>_<pov id>_yymmdd(hhmmss-hhmmss).[CFG|DAT|INFO|OMP]
        Сортирует по времени и формирует список файлов текущей страницы 
        (размера не более FILES_IN_PAGE) след. вида:
        [
         [<recorder_id>,<pov_id>, <from_yymmddhhmmss>, <to_yymmddhhmmss>, [<расширение1>, <расширение2>...]],
         [...]
        ]
        Например:
        [
         ['1', '0', '120119190000', '120119195959', ['.CFG', '.DAT', '.INFO'])
        ]

        '''
        
        nocache()

        page = int(page)

        entries = sorted(map(path.splitext, listdir(RECORDER_PATH)))
        cn = None
        files = []
        for n, e in entries:
            if cn != n:
                cn = n
                rec, pov, time = n.split('_')
                yymmddhhmmss1 = time[:6] + time[7:13]
                yymmddhhmmss2 = time[:6] + time[14:20]
                files.append([rec, pov, yymmddhhmmss1, yymmddhhmmss2, [e,]])
            else:
                files[-1][4].append(e)
        del entries
        pages= len(files)/FILES_IN_PAGE+1
        files.sort(key = lambda f: f[2])
        # выбор файлов текущей страницы
        files = files[(page-1)*FILES_IN_PAGE: min(len(files), page*FILES_IN_PAGE-1)] 
        return render.recfiles(page, pages, files, title = self.title)


