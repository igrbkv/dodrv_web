# -*- coding: utf-8 -*-
"""
1. Файл filters.conf записывается инсталлятором с параметрами: датчики, 
тип регистратора, общая частота дискретизации, частота тока, 
устройства, сигналы. Для РП4.06 в файле 6 каналов pov по 16/32 сигналов.  
При разборе отсутствующие каналы не удаляются, а только помечаются 
в параметре exists.
Минимальный файл конфигурации:
<?xml version="1.0" encoding="UTF-8"?>
<recorder id="0" station_name="П/с Долгоозерная" type="ПАРМА РП4.06" version="0.0">
    <ADCs>
        <ADC unit="V" coef2="0.0196" name="OV-0.2" checkout_AC="0.14" checkout_DC="0.2" checkout_Z="0.2" checkout_PE="3"/>
        ...
    </ADCs>
    <devices>
        <device id="0" in_use="yes" sample_rate="1800" frequency="50" analogs="16" discretes="32" skew="yes">
            <analogs>
                <analog id="0" in_use="yes" dc_component="0" ADC="MV-200" alias="Ia" coef1="1.0" phase="A"/>
                ...
            </analogs>
            <discretes>
                <discrete id="0" in_use="yes" inverted="yes" alias="Вкл." phase="" circuit_component=""/>
                ...
            </discretes>
        </device>
        <device id="1" in_use="yes" sample_rate="1800" frequency="50" analogs="16" discretes="32" skew="yes">
            ...
        </device>
        ...
        <device id="5" in_use="yes" sample_rate="1800" frequency="50" analogs="16" discretes="32" skew="yes">
            ...
        </device>
    </devices>
    <opc scan_rate_ms="100"/>
    <emergency prehistory_ms="200" after_history_ms="5000" max_file_length_s="10" keeping_period_days="1"/>
    <self-recorder live_update_ms="10000" analog_delta_percent="5" max_file_length_hour="1" keeping_time_days="1"/>
    <data_formats choice="comtrade">
        <comtrade codeset="CP1251" data_file="ASCII"/>
    </data_formats>
</recorder>
"""
import xml.sax
from os import path
from config import DEBUG_PATH
import syslog

__all__ = ['configXml', 'saveConfigXml']


ADCCOEF = 10./(1<<12)
DEFAULT_SAMPLE_RATE = 1800
SEP = '/'
DEV_PATH = DEBUG_PATH + '/dev/pov%s'

class ConfigParser(xml.sax.ContentHandler):
    state = 'parse' #'skip_analogs', 'skip_discretes', 'skip_analog', 'skip_filter'
    curDevice = None
    curAnalog = None
    curDiscrete = None
    curHarmonic = None
    curFilter = None
    curDiscretes = None
    
    recorder = None

    def __init__(self, fileName):
        xml.sax.handler.ContentHandler.__init__(self)
        parser = xml.sax.make_parser()
        parser.setContentHandler(self)
        try:
            parser.parse(fileName)
        except IOError, e:
            syslog.syslog('Ошибка (%i) при открытии файла %s' % (e.errno, e.filename))
            raise
        except:
            syslog.syslog('Ошибка разбора файла конфигурации', fileName)
            raise
    
    def _getObj(self, attr, al):
        d = {}
        for a in al:
            d[a] = attr.get(a)
        return d


    def startElement(self, tag, attr):
        #print tag
        if self.state != 'parse':
            return

        if tag == 'recorder':
            r = self._getObj(attr, ('id', 'station_name', 'type', 'version'))
            r['ADCs'] = {}
            r['device'] = {}
            self.recorder = r
        
        elif tag == 'ADC':
            self.recorder['ADCs'][attr.get('name')] = self._getObj(attr, ('coef2', 'unit', 'checkout_AC', 'checkout_DC', 'checkout_Z', 'checkout_PE'))

        elif tag == 'device':
            d = self._getObj(attr, ('in_use', 'analogs', 'discretes', 'sample_rate', 'frequency', 'skew'))
            d['analog'] = {}
            d['discrete'] = {}
            # отсутствующие каналы pov не удаляются, а только помечаются 
            # дополнительным параметром exists.
            d['exists'] = path.exists(DEV_PATH % attr.get('id'))
            self.recorder['device'][attr.get('id')] = d
            self.curDevice = attr.get('id')

        elif tag == 'analog':
            a = self._getObj(attr, ('id', 'in_use', 'dc_component', 'ADC', 'sinusoid', 'coef1', 'alias', 'phase', 'circuit_component'))
            self.curAnalog = a['id']
            self.recorder['device'][self.curDevice]['analog'][self.curAnalog] = a
     
        elif tag == 'rms':
            self.recorder['device'][self.curDevice]['analog'][self.curAnalog]['rms'] = self._getObj(attr, ('integration_interval_ms',))
            self.curFilter = tag
     
        elif tag == 'zero_phase_sequence' or \
            tag == 'positive_phase_sequence' or \
            tag == 'negative_phase_sequence':
            self.recorder['device'][self.curDevice]['analog'][self.curAnalog][tag] = self._getObj(attr, ('integration_interval_ms', 'id_b', 'id_c'))
            self.curFilter = tag

        elif tag == 'harmonic':
            self.recorder['device'][self.curDevice]['analog'][self.curAnalog][tag] = self._getObj(attr, ('integration_interval_ms', 'number'))
            self.curFilter = tag
     
        elif tag == 'active_power' or tag == 'reactive_power':
            self.recorder['device'][self.curDevice]['analog'][self.curAnalog][tag] = self._getObj(attr, ('integration_interval_ms', 'id_current'))
            self.curFilter = tag
         
        elif tag == 'analog_emergency':
            self.recorder['device'][self.curDevice]['analog'][self.curAnalog][self.curFilter][tag] = self._getObj(attr, ('top_threshold', 'bottom_threshold', 'max_duration_s'))
        
        elif tag == 'analog_self-recorder':
            self.recorder['device'][self.curDevice]['analog'][self.curAnalog][self.curFilter][tag] = self._getObj(attr, ('analog_delta_percent',))
        
        elif tag == 'analog_opc':
            self.recorder['device'][self.curDevice]['analog'][self.curAnalog][self.curFilter][tag] = {}

        elif tag == 'discrete':
            d = self._getObj(attr, ('id', 'in_use', 'inverted', 'alias', 'phase', 'circuit_component'))
            self.curDiscrete = d['id']
            self.recorder['device'][self.curDevice]['discrete'][self.curDiscrete] = d

        elif tag == 'trigger':
            self.recorder['device'][self.curDevice]['discrete'][self.curDiscrete]['trigger'] = self._getObj(attr, ('pulse_duration_ms', 'chatter_period_ms', 'chatter_suspend_threshold', 'chatter_resume_threshold'))

        elif tag == 'discrete_emergency':
            self.recorder['device'][self.curDevice]['discrete'][self.curDiscrete]['trigger']['discrete_emergency'] = {}
        
        elif tag == 'discrete_opc':
            self.recorder['device'][self.curDevice]['discrete'][self.curDiscrete]['trigger']['discrete_opc'] = {}
        
        elif tag == 'discrete_self-recorder':
            self.recorder['device'][self.curDevice]['discrete'][self.curDiscrete]['trigger']['discrete_self-recorder'] = {}

        elif tag == 'opc':
            self.recorder[tag] = self._getObj(attr, ('scan_rate_ms',))
        
        elif tag == 'emergency':
            self.recorder[tag] = self._getObj(attr, ('prehistory_ms', 'after_history_ms', 'max_file_length_s', 'keeping_period_days'))
        
        elif tag == 'self-recorder':
            self.recorder[tag] = self._getObj(attr, ('live_update_ms', 'analog_delta_percent', 'max_file_length_hour', 'keeping_time_days'))
        
        elif tag == 'data_formats':
            self.recorder[tag] = self._getObj(attr, ('choice',))
        
        elif tag == 'comtrade':
            self.recorder['data_formats'][tag] = self._getObj(attr, ('codeset', 'data_file'))

    def endElement(self, tag):
        if tag == 'device':
            self.curDevice = None
        elif tag == 'analog':
            #print self.recorder['device'][self.curDevice]['analog'][self.curAnalog]
            self.curAnalog = None
        elif tag == 'discrete':
            self.curDiscrete = None
        elif tag in ('rms', 'zero_phase_sequence', 
            'positive_phase_sequence', 'negative_phase_sequence',
            'harmonic', 'active_power', 'reactive_power'):
            self.curFilter = None
    

def configXml(filePath):
    parser = None
    try:
        parser = ConfigParser(filePath)
    except:
        raise         
    else:
        return parser.recorder


if __name__ == '__main__':
    rcd = configXml('config.xml')
