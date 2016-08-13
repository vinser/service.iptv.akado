#
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Kodi; see the file COPYING.  If not, see
#  <http://www.gnu.org/licenses/>.
#
#
#
#   Add-On by VinSer for watching Akado IPTV with PVR IPTV Simple Client Kodi Add-on   
#   Many statements were taken from Add-Ons written by unselfish people, many thanks them all
#   You can aslo do it with this Add-On freely
#

#!/usr/bin/python
# -*- coding: utf-8 -*-


import xbmc
import xbmcaddon
import os.path
import xml.etree.ElementTree as ET
import urllib2
from datetime import datetime, timedelta
from operator import itemgetter

#   Constants
ADDON        = xbmcaddon.Addon()
ADDONVERSION = ADDON.getAddonInfo('version')
ADDONNAME    = ADDON.getAddonInfo('name')
ADDONPATH    = ADDON.getAddonInfo('path').decode('utf-8')
ADDONPROFILE = xbmc.translatePath( ADDON.getAddonInfo('profile') ).decode('utf-8')
ICON         = ADDON.getAddonInfo('icon')

MONITOR = xbmc.Monitor()
LOGLEVEL = xbmc.LOGNOTICE

AKADO_CHANNELS_URL = 'https://wintray.akado-ural.ru/wintray.php?action=media'
AKADO_EPG_URL = 'https://wintray.akado-ural.ru/misc/telecast.xml'
iptv_files_name = 'AkadoIPTV'

# Settings
set_refresh_period = int(ADDON.getSetting('refresh_period'))*60
set_iptv_files_folder = ADDON.getSetting('files_folder')
set_tvg_shift = ADDON.getSetting('tvg_shift')

# Functions

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode('utf-8')
    message = u'%s(%s): %s' % (ADDONNAME, datetime.now().strftime('%Y.%m.%d %H:%M:%S,%f'), txt)
    xbmc.log(msg=message.encode('utf-8'), level=LOGLEVEL)

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def wait_video_end():
    while xbmc.Player().isPlayingVideo() and not MONITOR.abortRequested():
        if MONITOR.waitForAbort(1):
            break
#    i = 0
#    while i < 10 and not MONITOR.abortRequested():
#        if MONITOR.waitForAbort(1):
#            break
#        i += 1

def cook_channel_list():
    response = urllib2.urlopen(AKADO_CHANNELS_URL)
   
    if not response or response.getcode() != 200:
        raise IOError('Wrong response code')
    
    url_root = ET.fromstring(response.read())
    ch_list = []
    for stream in url_root.findall('./streams/stream'):
        ch_list.append((stream.attrib['title'].encode('utf-8'), stream.attrib['id'], stream.attrib['uri'])) 
        
    with open(os.path.join(set_iptv_files_folder, iptv_files_name)+'.m3u', 'w') as f:
        f.write('#EXTM3U tvg-shift=' + set_tvg_shift + '\n')
        for rec in sorted(ch_list, key=itemgetter(0)):
            title, id, uri = rec
            f.write('#EXTINF:-1'
                 + ' tvg-shift="0"' 
                 + ' tvg-id="' + id + '"'
                 + ' tvg-logo="' + id + '.png"'
                 + ' group-title="AKADO"'
                 + ', ' + title + '\n')
            f.write( uri + '\n')


def cook_epg():
    epg_root = ET.Element('tv')
    response = urllib2.urlopen(AKADO_EPG_URL)
   
    if not response or response.getcode() != 200:
        raise IOError('Wrong response code')

    url_root = ET.fromstring(response.read())
    for program in url_root.iter('program'):
        channel = ET.SubElement(epg_root, 'channel', {'id':program.attrib['id']})
        ET.SubElement(channel, 'display-name', {'lang':'ru'}).text = program.find('title').text.replace('![CDATA[','').replace(']]','')
        ET.SubElement(channel, 'icon')
        for item in program.iter('item'):
            if datetime.now() + + timedelta(hours=-4) <= datetime.fromtimestamp(float(item.find('start').text)) < (datetime.now() + timedelta(hours=12)):
                programme = ET.SubElement(epg_root, 'programme', {'start':epg_time(item.find('start').text),
                                                                  'stop':epg_time(item.find('stop').text),
                                                                  'channel':program.attrib['id']})
                ET.SubElement(programme, 'title', {'lang':'ru'}).text = item.find('title').text
                ET.SubElement(programme, 'desc', {'lang':'ru'}).text = item.find('descr').text
#    ETR(epg_root).write(os.path.join(set_iptv_files_folder, iptv_files_name)+'.xml', encoding='utf-8')
    indent(epg_root)
    ET.ElementTree(epg_root).write(os.path.join(set_iptv_files_folder, iptv_files_name)+'.xml', encoding='utf-8', xml_declaration=True)    
   
def epg_time(sdt):
    dt = datetime.fromtimestamp(float(sdt))
    return dt.strftime('%Y%m%d%H%M%S') + '+0000'
    
# main
def main():
    #xbmc.sleep(5000)
    log('%s ver.%s started' % (ADDONNAME, ADDONVERSION))
    
    #pvr_restarted = True
    while not MONITOR.abortRequested():
        wait_video_end()
        cook_channel_list()
        cook_epg()
        log('IPTV files were refreshed')
        #if not pvr_restarted:
        #    pvr_restarted = True
        #    xbmc.executebuiltin('XBMC.StartPVRManager')
        if MONITOR.waitForAbort(set_refresh_period):
            break
    log('ABORT REQUESTED')
        
if (__name__ == '__main__'):
    if len(ADDON.getSetting('files_folder')) != 0: main()
