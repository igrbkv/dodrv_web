# -*- coding: utf-8 -*-

import web
from web import form
from config import render, xml, EMERGENCY_PATH, RECORDER_PATH, FILES_IN_PAGE
from http import nocache
from os import listdir, path

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
         ['1', '0', '120119190000100', ['.cfg', '.dat', '.inf'])
        ]

        '''
        page = int(page)

        nocache()

        entries = sorted(map(path.splitext, listdir(EMERGENCY_PATH)))
        cn = None
        files = []
        for n, e in entries:
            if e in ['.cfg', '.dat', '.inf']:
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
        pages = (len(files)+FILES_IN_PAGE-1)/FILES_IN_PAGE
        files.sort(key = lambda f: f[2])
        # выбор файлов текущей страницы
        files = files[(page-1)*FILES_IN_PAGE: min(len(files), page*FILES_IN_PAGE)] 
        return render.emgfiles(page, pages, files, title = self.title)

class Recorders:
    title = 'Файлы самописца'

    def GET(self, page='1'):
        '''
        Считывает все файлы из папки RECORDER_PATH
        <recorder id>_<pov id>_yymmdd(hhmmss-hhmmss).[CFG|DAT]
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
            if e in ['.cfg', '.dat']:
                if cn != n:
                    cn = n
                    rec, pov, time = n.split('_')
                    time = time.replace('(', '');
                    time = time.replace(')', '');
                    beg, end = time.split('-')
                    end = beg[:len(beg)-len(end)]+end
                    files.append([rec, pov, beg, end, n, [e,]])
                else:
                    files[-1][5].append(e)
        del entries
        pages = (len(files)+FILES_IN_PAGE+1)/FILES_IN_PAGE
        files.sort(key = lambda f: f[2])
        # выбор файлов текущей страницы
        files = files[(page-1)*FILES_IN_PAGE: min(len(files), page*FILES_IN_PAGE)] 
        return render.recfiles(page, pages, files, title = self.title)


