versione='1.2.77'
# Module: launcher
# Author: ElSupremo
# Created on: 22.02.2021
# Last update: 05.01.2026
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
import os
import logging
import xbmcgui
import xbmc
import xbmcplugin
import xbmcaddon
import json
import string
import random
import re
import time
import xbmcvfs

# Get the plugin url in plugin:// notation. 
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
addon_id = 'plugin.video.mandrakodi'
#selfAddon = xbmcaddon.Addon(id=addon_id)
xbmcaddon.Addon(id=addon_id).setSetting("debug", "on")

debug = xbmcaddon.Addon(id=addon_id).getSetting("debug")
showAdult = xbmcaddon.Addon(id=addon_id).getSetting("ShowAdult")
lastView = xbmcaddon.Addon(id=addon_id).getSetting("urlAppo1")
if (lastView=="Not in use"):
    lastView="51"
testoLog = "";
viewmode=lastView
ua = ""

autoView="Not in use"
try:
    autoView = xbmcaddon.Addon(id=addon_id).getSetting("urlAppo4")
except:
    pass
if (autoView=="Not in use"):
    autoView="1"

PY3 = sys.version_info[0] == 3
if PY3:
    from urllib.parse import urlencode, parse_qsl
else:
    from urlparse import urlparse, parse_qsl
    from urllib import urlencode, quote
	
def logga(mess):
    global testoLog
    if debug == "on":
        logging.warning("MANDRA_LOG: \n"+mess)
        testoLog += mess+"\n";

def makeRequestNoUa(url):
    logga('TRY TO OPEN '+url)
    html = ""
    if PY3:
        import urllib.request as myRequest
    else:
        import urllib2 as myRequest
    try:
        req = myRequest.Request(url)
        response = myRequest.urlopen(req, timeout=45)
        html = response.read().decode('utf-8')
        response.close()
        retff="NOCODE"
        if html != "":
            retff=html[0:15]
        logga('OK REQUEST FROM '+url+' resp: '+retff)
    except:
        logging.warning('Error to open url: '+url)
        pass
    return html


def makeRequest(url, hdr=None):
    logga('TRY TO OPEN '+url)
    html = ""
    if PY3:
        import urllib.request as myRequest
    else:
        import urllib2 as myRequest
    pwd = xbmcaddon.Addon(id=addon_id).getSetting("password")
    deviceId = xbmcaddon.Addon(id=addon_id).getSetting("urlAppo2")
    if (deviceId == "Not in use" or deviceId == "" or len(deviceId) != 6):
        #generate id
        deviceId = id_generator()
        xbmcaddon.Addon(id=addon_id).setSetting("urlAppo2", deviceId)
    version = xbmcaddon.Addon(id=addon_id).getAddonInfo("version")
    if hdr is None:
        ua = "MandraKodi2@@"+version+"@@"+pwd+"@@"+deviceId
        hdr = {"User-Agent" : ua}
    try:
        req = myRequest.Request(url, headers=hdr)
        response = myRequest.urlopen(req, timeout=45)
        html = response.read().decode('utf-8')
        response.close()
        retff="NOCODE"
        if html != "":
            retff=html[0:15]
        logga('OK REQUEST FROM '+url+' resp: '+retff)
    except:
        logging.warning('Error to open url: '+url)
        pass
    return html

def getSource():
    startUrl = "https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/data/disclaimer.json"
    #startUrl = "https://www.dropbox.com/s/igyq58cnpjq0fq4/disclaimer.json?dl=1"
    try:
        strSource = makeRequest(startUrl)
        if strSource is None or strSource == "":
            logging.warning('MANDRA_LOG: NO DISCLAIMER')
            strSource = underMaintMsg()
        else:
            logga('OK SOURCE ')
            liveVersion = "Mandrakodi "+str(xbmcaddon.Addon(id=addon_id).getAddonInfo("version"))
            strSource=strSource.replace("Mandrakodi 2.0", liveVersion)
    except Exception as err:
        errMsg="ERRORE: {0}".format(err)
        logging.warning("MANDRA_LOG: UNDER MAINTENANCE \n"+errMsg)
        strSource = underMaintMsg()
        pass
    jsonToItems(strSource)

def underMaintMsg():
    strToRet = '{"SetViewMode":"500","items":['
    strToRet +='{"title":"[COLOR red]ADDON UNDER MAINTENANCE[/COLOR]",'
    strToRet +='"link":"ignore","thumbnail":"https://images-na.ssl-images-amazon.com/images/I/41sxqlFU88L.jpg",'
    strToRet +='"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg","info":"Addon Under Maintenance"},'
    strToRet +='{"title":"[COLOR gold]SEND LOG[/COLOR]",'
    strToRet +='"log":"ignore","thumbnail":"https://e7.pngegg.com/pngimages/584/374/png-clipart-green-computer-monitor-computer-monitor-accessory-screen-multimedia-11-computer-matrix-computer-computer-monitor-accessory-thumbnail.png",'
    strToRet +='"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg","info":"Send Log"}'
    strToRet +=']}'

    return strToRet

def connProblemMsg():
    strToRet = '{"SetViewMode":"500","items":['
    strToRet +='{"title":"[COLOR red]CONNECION PROBLEM[CR]TRY LATER.[/COLOR]",'
    strToRet +='"link":"ignore","thumbnail":"https://images-na.ssl-images-amazon.com/images/I/41sxqlFU88L.jpg",'
    strToRet +='"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg","info":"Addon Under Maintenance"},'
    strToRet +='{"title":"[COLOR gold]SEND LOG[/COLOR]",'
    strToRet +='"log":"ignore","thumbnail":"https://e7.pngegg.com/pngimages/584/374/png-clipart-green-computer-monitor-computer-monitor-accessory-screen-multimedia-11-computer-matrix-computer-computer-monitor-accessory-thumbnail.png",'
    strToRet +='"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg","info":"Send Log"}'
    strToRet +=']}'

    return strToRet

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def play_video(path):
    urlClean=path.replace(" ", "%20")
    play_item = xbmcgui.ListItem(path=urlClean)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def getTxtMessage(vName):
    home = ''
    if PY3:
        home = xbmcvfs.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
    else:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path').decode('utf-8'))
    fPath = os.path.join(home, vName)
    resF = open(fPath)
    file_content = resF.read()
    resF.close()
    return file_content

def getExternalJson(strPath):
    strSource = makeRequest(strPath)
    #strSource = makeRequestNoUa(strPath)
    if (strSource == ""):
        msgBox("Spiacenti, la fonte non e' raggiungibile")
        remoteLog("NO_FONTE@@"+strPath)
        logging.warning("NO JSON AT: "+strPath)
        strSource = connProblemMsg()
    
    jsonToItems(strSource)
	
def jsonToItems(strJson):
    global viewmode
    try:
        logga('START jsonToItems')
        dataJson = json.loads(strJson)
    except Exception as err:
        errMsg="Errore: Nessuna risposta dal server (No Json)"
        msgBox(errMsg)
        writeFileLog("BAD_JSON\n"+strJson, "w+")
        return
    
    xbmcplugin.setContent(_handle, 'movies')
    
    try:
        nvs = dataJson['name']
        if nvs == addon_id:
            vS = dataJson['groups'][0]["stations"][0]["url"]
            if not vS.startswith("http"):
                return jsonToItems(getTxtMessage(vS))
            return getExternalJson(vS)
    except:
        pass

    try:
        viewmode = dataJson['SetViewMode']
        skin_name = xbmc.getSkinDir()
        logga("view mode for "+skin_name+" on "+viewmode)
    except:
        viewmode = "51"
        logga('no view mode')
        pass
    
    try:
        arrChan = dataJson['channels']
        logga("OK CHANNELS")
        return jsonToChannels(strJson)
    except:
        logga('NO CHANNELS. GetItems')
        pass
    
    link = ""
    strLog=""
    try:
        for item in dataJson["items"]:
            strLog=json.dumps(item)
            titolo = "NO TIT"
            thumb = "https://www.andreisfina.it/wp-content/uploads/2018/12/no_image.jpg"
            fanart = "https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
            genre = "generic"
            info = ""
            regExp = ""
            resolverPar = "no_par"
            
            tipoLink = ""
            
            extLink = False
            extLink2 = False
            is_folder = False
            is_magnet = False
            is_myresolve = False
            is_regex = False
            is_m3u = False
            is_chrome = False
            is_yatse = False
            is_pvr = False
            is_log = False
            is_copyXml = False
            is_updateCode = False
            is_delSet = False
            is_personal = False
            is_enabled = True

            if 'enabled' in item:
                is_enabled = item["enabled"]
            if is_enabled == False:
                continue

            if 'tipoLink' in item:
                tipoLink = item["tipoLink"]
                if tipoLink == "adult":
                    if showAdult=="false":
                        continue
            
                if tipoLink == "android":
                    if (xbmc.getCondVisibility("system.platform.android") == False):
                        continue
            
            if 'title' in item:
                titolo = item["title"]
            if 'thumbnail' in item:
                thumb = item["thumbnail"]
            if 'fanart' in item:
                fanart = item["fanart"]
            if 'info' in item:
                info = item["info"]
            if 'genre' in item:
                genre = item["genre"]
            if 'link' in item:
                link = item["link"]
                if 'youtube' in link:
                    is_yatse = True
                    is_folder = True
            if 'acelocal' in item:
                link = "http://127.0.0.1:6878/ace/getstream?id="+item["acelocal"]
            if 'acehls' in item:
                link = "http://127.0.0.1:6878/ace/manifest.m3u8?id="+item["acehls"]
            if 'externallink' in item:
                extLink = True
                is_folder = True
                link = item["externallink"]
            if 'externallink2' in item:
                extLink2 = True
                is_folder = True
                link = item["externallink2"]
            if 'myresolve' in item:
                is_myresolve = True
                is_folder = True
                link = item["myresolve"]
                #logga("MY_RESOLVE_LINK: "+link)
                if "@@" in link:
                    arrT=link.split("@@")
                    link=arrT[0]
                    resolverPar=arrT[1]
                elif ":" in link:
                    arrT=link.split(":")
                    link=arrT[0]
                    resolverPar=arrT[1]
                #logga("MY_RES_LINK: "+link)
                #logga("MY_RES_PAR: "+resolverPar)
            if 'regexPage' in item:
                is_regex = True
                link = item["regexPage"]
                if 'regexExpres' in item:
                    regExp = item["regexExpres"]
            if 'chrome' in item:
                is_chrome = True
                is_folder = True
                link = item["chrome"]
            if 'yatse' in item:
                is_yatse = True
                #is_folder = True
                link = item["yatse"]
            if 'm3u' in item:
                is_m3u = True
                is_folder = True
                link = item["m3u"]
            if 'personal' in item:
                is_personal = True
                is_folder = True
                link = item["personal"]
            if 'magnet' in item:
                is_magnet = True
                link = item["magnet"]
            if 'pvr' in item:
                is_pvr = True
                link = item["pvr"]
            if 'log' in item:
                is_log = True
                is_folder = True
                link = "ignore"
            if 'copyXml' in item:
                is_copyXml = True
                is_folder = True
                link = item["copyXml"]
            if 'updateCode' in item:
                is_updateCode = True
                is_folder = True
                link = item["updateCode"]
            if 'delSet' in item:
                is_delSet = True
                is_folder = True
                link = item["delSet"]
            list_item = xbmcgui.ListItem(label=titolo)
            list_item.setInfo('video', {'title': titolo,'genre': genre,'plot': info,'mediatype': 'movie','credits': 'ElSupremo'})
            list_item.setArt({'thumb': thumb, 'icon': thumb, 'poster': thumb, 'landscape': fanart, 'fanart': fanart})
            url = ""

            if extLink == True:
                url = get_url(action='getExtData', url=link)
            elif extLink2 == True:
                url = get_url(action='getExtData2', url=link)
            elif is_regex == True:
                list_item.setProperty('IsPlayable', 'true')
                url = get_url(action='regex', url=link, exp=regExp)
            elif is_myresolve == True:
                url = get_url(action='myresolve', url=link, parIn=resolverPar)
            elif is_pvr == True:
                url = get_url(action='pvr', url=link)
            elif is_log == True:
                url = get_url(action='log', url=link)
            elif is_m3u == True:
                url = get_url(action='m3u', url=link)
            elif is_personal == True:
                url = get_url(action='personal', url=link)
            elif is_copyXml == True:
                url = get_url(action='copyXml', url=link)
            elif is_updateCode == True:
                url = get_url(action='updateCode', url=link)
            elif is_delSet == True:
                url = get_url(action='delSet', url=link)
            elif is_yatse == True:
                list_item.setProperty('IsPlayable', 'true')
                arrT=link.split("@@")
                tipo=arrT[0]
                link1=arrT[1]
                if tipo=="pls":
                    url = get_urlYatse(playlist_id=link1)
                else:
                    url = get_urlYatse(video_id=link1)
                #url = get_urlYatse(action='share', type='unresolvedurl', data=link)
            elif is_magnet == True:
                list_item.setProperty('IsPlayable', 'true')
                url = get_urlMagnet(uri=link)
            elif is_chrome == True:
                url = get_urlChrome(mode='showSite', stopPlayback='no', kiosk='no', url=link)
            else:
                if 'apk' in item:
                    logga('APK MODE')
                    list_item.setProperty('IsPlayable', 'true')
                    is_folder = True
                    apkName=item["apk"]
                    url = get_url(action='apk', url=link, apk=apkName)
                else:
                    list_item.setProperty('IsPlayable', 'true')
                    if not link.startswith("plugin://plugin"):
                        url = get_url(action='play', url=link)
                    else:
                        url = get_url(action='plugin', url=link)
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        logga("CALL LAUNCHER endOfDirectory 1")
        xbmcplugin.endOfDirectory(_handle)
    except:
        import traceback
        msgBox("Errore nella lettura del json")
        remoteLog("NO_JSON_READ@@"+strLog)
        writeFileLog("NO_JSON_READ\n"+strLog, "w+")
        traceback.print_exc()
        #logging.warning(strJson)


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_urlMagnet(**kwargs):
    return '{0}?{1}'.format("plugin://plugin.video.elementum/play", urlencode(kwargs))

def get_urlChrome(**kwargs):
    return '{0}?{1}'.format("plugin://plugin.program.browser.launcher/", urlencode(kwargs))

def get_urlYatse(**kwargs):
    #return "plugin://plugin.video.youtube/play/?"+ppa+"="+link
    return '{0}?{1}'.format("plugin://plugin.video.youtube/play/", urlencode(kwargs))
    #return '{0}?{1}={2}'.format("plugin://plugin.video.youtube/play/", ppa, urlencode(link))

def parameters_string_to_dict(parameters):
    params = dict(parse_qsl(parameters.split('?')[1]))
    return params

def jsonToChannels(strJson):
    jobStep=1
    jobCh=1
    try:
        channelsArray = json.loads(strJson)
        jobStep += 1
        window = xbmcgui.Window(10000)
        window.setProperty("chList", strJson)
        xbmcplugin.setContent(_handle, 'movies')
        for channel in channelsArray["channels"]:
            jobCh=1
            jobStep += 1
            titolo = "NO TIT"
            thumb = "https://www.andreisfina.it/wp-content/uploads/2018/12/no_image.jpg"
            fanart = "https://www.andreisfina.it/wp-content/uploads/2018/12/no_image.jpg"
            genre = "generic"
            info = ""
            is_enabled = True

            if 'enabled' in channel:
                is_enabled = channel["enabled"]
            if is_enabled == False:
                continue

            if 'name' in channel:
                try:
                    titolo = channel["name"]
                except:
                    titolo = "NO_TIT"
                jobCh += 1
            if 'thumbnail' in channel:
                thumb = channel["thumbnail"]
                jobCh += 1
            if 'fanart' in channel:
                fanart = channel["fanart"]
                jobCh += 1
            if 'info' in channel:
                info = channel["info"].encode('utf-8').strip()
                jobCh += 1
            list_item = xbmcgui.ListItem(label=titolo)
            jobCh += 1
            list_item.setInfo('video', {'title': titolo,'genre': genre,'plot': info,'mediatype': 'movie','credits': 'ElSupremo'})
            jobCh += 1
            list_item.setArt({'thumb': thumb, 'icon': thumb, 'poster': thumb, 'landscape': fanart, 'fanart': fanart})
            jobCh += 1
            url = get_url(action='getChannel', url=titolo)
            jobCh += 1
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
            jobCh += 1
        logga("CALL LAUNCHER endOfDirectory 2")
        xbmcplugin.endOfDirectory(_handle)
    except Exception as err:
        import traceback
        logging.warning("ERR_TIT: "+titolo)
        
        msgBox("Errore nella creazione delle gategorie: "+str(jobStep)+" - "+str(jobCh))
        traceback.print_exc()    
   
def channelToItems(strChName, _handle):
    window = xbmcgui.Window(10000)
    strJson = window.getProperty("chList")
    channelsArray = json.loads(strJson)
    xbmcplugin.setContent(_handle, 'movies')
    for channel in channelsArray["channels"]:
        titolo = channel["name"]
        if titolo == strChName:
            logga("FOUND CH: "+titolo)
            jsonToItems(json.dumps(channel))

def simpleRegex(page, find):
    hdr = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}
    html = makeRequest(page, hdr)
    #if PY3:
        #html = html.decode('utf-8')
    logga("HTML:\n"+html)		
    urlSteam = re.findall(find, html)[0]
    logga("urlSteam:\n"+urlSteam)	
    return urlSteam

def jsonrpcRequest(method, params=None):
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params if params else {},
        "id": 1
    }

    response = xbmc.executeJSONRPC(json.dumps(request))
    return json.loads(response)

def getInstalledVersion():
    kodiVersionInstalled = 0
    # retrieve kodi installed version
    jsonProperties = jsonrpcRequest("Application.GetProperties", {"properties": ["version", "name"]})
    kodiVersionInstalled = str(jsonProperties['result']['version']['major'])+"@@"+str(jsonProperties['result']['version']['minor'])
    
    return kodiVersionInstalled


def callReolver(metodo, parametro):
    global viewmode
    import myResolver
    thumb="https://static.vecteezy.com/system/resources/previews/018/842/642/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
    thumb="https://icons.iconarchive.com/icons/double-j-design/ravenna-3d/256/Play-icon.png"
    fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        
    if metodo=="daddy" and "dlhd.so" in parametro:
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://techvig.net/wp-content/uploads/2022/07/Daddylive-Alternative-2022.png"
        logga("CALL myResolver.PlayStream for "+parametro)
        if checkPluginInstalled("inputstream.ffmpegdirect") == False:
            msgBox("Installare il plugin [B]inputstream.ffmpegdirect[/B] dalla repository di Kodi > Lettore video InputStream")
            return
        arrL=parametro.split("stream-")
        codeIn=arrL[1].replace(".php", "")
        newTit="[COLOR lime]PLAY STREAM DADDY "+codeIn+"[/COLOR]"
        list_item = myResolver.PlayStream(codeIn)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'videos')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="scws3":
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://png.pngtree.com/png-vector/20230124/ourmid/pngtree-arrow-icon-3d-play-png-image_6565151.png"
        newTit="[COLOR lime]PLAY SC MOVIE[/COLOR]"
        list_item = myResolver.scwsNew(parametro, 1)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="amstaff":
        kodi_version=getInstalledVersion()
        arrVer=kodi_version.split("@@")
        kodi_vers=int(arrVer[0])
        kodi_minVers=int(arrVer[1])
        if kodi_vers<21 or (kodi_vers==21 and kodi_minVers<1):
            msgBox("Per visualizzare questo link, e' necessaria la versione [B]21.1[/B], o superiore, di Kodi ["+str(kodi_vers)+"."+str(kodi_minVers)+"]")
            return
        
        if checkPluginInstalled("inputstream.adaptive") == False:
            msgBox("Installare il plugin [B]inputstream.adaptive[/B] dalla repository di Kodi > Lettore video InputStream")
            return
        
        version = xbmcaddon.Addon(id="inputstream.adaptive").getAddonInfo("version")
       
        arrVerAd = version.split(".")
        major = int(arrVerAd[0])
        medium = int(arrVerAd[1])
        minor = int(arrVerAd[2])

        if major<21 or (major==21 and medium < 5) or (major==21 and medium == 5 and minor < 4):
            msgBox("Per visualizzare questo link, e' necessaria la versione [B]21.5.4[/B], o superiore, di [B]inputstream.adaptive[/B] ["+str(major)+"."+str(medium)+"."+str(minor)+"]")
            return

        pwd = xbmcaddon.Addon(id=addon_id).getSetting("password")
        urlSup="https://test34344.herokuapp.com/testAnonym.php?token="+pwd+"&dns1=AMSTAFF&dns2="+version
        #makeRequestNoUa(urlSup)
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://png.pngtree.com/png-vector/20230124/ourmid/pngtree-arrow-icon-3d-play-png-image_6565151.png"
        newTit="[COLOR lime]PLAY STREAM[/COLOR]"
        
        list_item = myResolver.amstaffTest(parametro)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="daznToken":
        kodi_version=getInstalledVersion()
        arrVer=kodi_version.split("@@")
        kodi_vers=int(arrVer[0])
        kodi_minVers=int(arrVer[1])
        if kodi_vers<21 or (kodi_vers==21 and kodi_minVers<1):
            msgBox("Per visualizzare questo link, e' necessaria la versione [B]21.1[/B], o superiore, di Kodi ["+str(kodi_vers)+"."+str(kodi_minVers)+"]")
            return
        
        if checkPluginInstalled("inputstream.adaptive") == False:
            msgBox("Installare il plugin [B]inputstream.adaptive[/B] dalla repository di Kodi > Lettore video InputStream")
            return
        
        version = xbmcaddon.Addon(id="inputstream.adaptive").getAddonInfo("version")
       
        arrVerAd = version.split(".")
        major = int(arrVerAd[0])
        medium = int(arrVerAd[1])
        minor = int(arrVerAd[2])

        if major<21 or (major==21 and medium < 5) or (major==21 and medium == 5 and minor < 4):
            msgBox("Per visualizzare questo link, e' necessaria la versione [B]21.5.4[/B], o superiore, di [B]inputstream.adaptive[/B] ["+str(major)+"."+str(medium)+"."+str(minor)+"]")
            return

        pwd = xbmcaddon.Addon(id=addon_id).getSetting("password")
        urlSup="https://test34344.herokuapp.com/testAnonym.php?token="+pwd+"&dns1=AMSTAFF&dns2="+version
        #makeRequestNoUa(urlSup)
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://png.pngtree.com/png-vector/20230124/ourmid/pngtree-arrow-icon-3d-play-png-image_6565151.png"
        newTit="[COLOR lime]PLAY STREAM[/COLOR]"
        #logga("CALL myResolver.amstaff for "+parametro)
        list_item = myResolver.daznToken(parametro)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="antena":
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://static.vecteezy.com/system/resources/previews/018/842/688/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
        newTit="[COLOR lime]PLAY STREAM[/COLOR]"
        logga("CALL myResolver.antena for "+parametro)
        list_item = myResolver.antena(parametro)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="daddyP":
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://static.vecteezy.com/system/resources/previews/018/842/688/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
        newTit="[COLOR lime]PLAY DADDY[/COLOR]"
        logga("CALL myResolver.daddyPremium for "+parametro)
        list_item = myResolver.daddyPremium(parametro)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="huhu":
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://static.vecteezy.com/system/resources/previews/018/842/688/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
        newTit="[COLOR lime]PLAY STREAM[/COLOR]"
        logga("CALL myResolver.huhu for "+parametro)
        list_item = myResolver.huhu(parametro)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="sky":
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://static.vecteezy.com/system/resources/previews/018/842/688/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
        newTit="[COLOR lime]PLAY STREAM[/COLOR]"
        logga("CALL myResolver.sky for "+parametro)
        list_item = myResolver.sky(parametro)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="ffmpeg":
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://static.vecteezy.com/system/resources/previews/018/842/688/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
        newTit="[COLOR lime]PLAY STREAM[/COLOR]"
        logga("CALL myResolver.ffmpeg for "+parametro)
        list_item = myResolver.ffmpeg(parametro)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="ffmpeg_noRef":
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://static.vecteezy.com/system/resources/previews/018/842/688/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
        newTit="[COLOR lime]PLAY STREAM[/COLOR]"
        logga("CALL myResolver.ffmpeg_noRef for "+parametro)
        list_item = myResolver.ffmpeg_noRef(parametro)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif metodo=="mpd":
        logga("PAR: "+parametro)
        arrTmp=parametro.split("____")
        link=arrTmp[0]
        newTit="[COLOR lime]PLAY MPD[/COLOR]"
        try:
            newTit="[COLOR lime]PLAY "+arrTmp[1]+"[/COLOR]"
        except:
            pass
        fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
        img="https://static.vecteezy.com/system/resources/previews/018/842/688/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
       
        logga("CALL myResolver.play_mpd for "+link)
        list_item = myResolver.play_mpd(link)
        list_item.setLabel(newTit)
        list_item.setLabel2(newTit)
        list_item.setArt({'thumb': img, 'icon': img, 'poster': img, 'landscape': fanart, 'fanart': fanart})
        url=list_item.getPath()
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    else:
        retVal = myResolver.run(metodo, parametro)

        if retVal == None:
            return
        xbmcplugin.setContent(_handle, 'movies')
        if isinstance(retVal, list):
            numLink=1
            oldLink="";
            for linkTmp in retVal:
                newList=list(linkTmp)
                newLink=newList[0]
                newP=newList[1]
                info=""
                if len(newList)>2:
                    info=newList[2]
                    viewmode="503"

                if len(newList)>3:
                    thumb=newList[3]
                
                if len(newList)>4:
                    tipo=newList[4]
                    if tipo == "json":
                        return jsonToItems(newLink)

                logga("Stream_Url ==> " + newLink)
                logga("Stream_Tit ==> " + newP)
                newTit="[COLOR lime]PLAY LINK "+str(numLink)+" ("+newLink[0:4]+")[/COLOR]"
                if newP != "":
                    newTit=newP
                list_item = xbmcgui.ListItem(label=newTit)
                list_item.setInfo('video', {'title': newTit,'plot': info,'mediatype': 'movie','credits': 'ElSupremo'})
                list_item.setArt({'thumb': thumb, 'icon': thumb, 'poster': thumb, 'landscape': fanart, 'fanart': fanart})
                list_item.setProperty('IsPlayable', 'true')
                url = get_url(action='play', url=newLink)
                if oldLink!=newLink:
                    oldLink=newLink
                    xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
                    numLink += 1
        else:
            logga("StreamUrl ==> " + retVal)
            newTit="[COLOR lime]PLAY LINK ("+retVal[0:4]+")[/COLOR]"
            list_item = xbmcgui.ListItem(label=newTit)
            list_item.setInfo('video', {'title': newTit,'genre': 'generic','mediatype': 'movie','credits': 'ElSupremo'})
            list_item.setArt({'thumb': thumb, 'icon': thumb, 'poster': thumb, 'landscape': fanart, 'fanart': fanart})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', url=retVal)
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    ppop=0    
    if metodo != "mac" and metodo != "scws" and ppop==1:
        viewmode="51"
        newTit="[COLOR gold]OPEN WEB LINK (WISE)[/COLOR]"
        list_item = xbmcgui.ListItem(label=newTit)
        list_item.setInfo('video', {'title': newTit,'genre': 'generic','mediatype': 'movie','credits': 'ElSupremo'})
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'poster': thumb, 'landscape': fanart, 'fanart': fanart})
        list_item.setProperty('IsPlayable', 'true')
        newUrl2=parametro
        if "?" in parametro:
            newUrl2 += "&extPL=wise"
        else:
            newUrl2 += "?extPL=wise"
        url = get_url(action='play', url=newUrl2)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    
    logga("CALL LAUNCHER endOfDirectory 3")
    xbmcplugin.endOfDirectory(_handle)

def runApk(apkName, apkPar):
    xbmc.executebuiltin('StartAndroidActivity("'+apkName+'", "android.intent.action.VIEW", "", "'+apkPar+'")')

def getPvr():
    myPvr = None
        
    if not os.path.exists(xbmcvfs.translatePath('special://home/addons/pvr.iptvsimple')) and not os.path.exists(xbmcvfs.translatePath('special://xbmcbinaddons/pvr.iptvsimple')):
        xbmc.executebuiltin('InstallAddon(pvr.iptvsimple)', wait=True)
    
    pvr_enabled = '"enabled":true' in xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","id":1,"params":{"addonid":"pvr.iptvsimple", "properties": ["enabled"]}}')
    if (not pvr_enabled):
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "pvr.iptvsimple", "enabled": true }}')
    
    myPvr = xbmcaddon.Addon(id='pvr.iptvsimple')
    return myPvr

def setPvr(urlM3u):
    try:
        pvrSimpleTv=getPvr()
        
        if PY3:
            xbmc.executebuiltin('xbmc.StopPVRManager')
        else:
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "pvr.iptvsimple", "enabled": false }}')
        if pvrSimpleTv.getSetting('m3uPathType') != '1': 
            pvrSimpleTv.setSetting('m3uPathType', '1')
        pvrSimpleTv.setSetting('epgUrl','')
        pvrSimpleTv.setSetting('m3uUrl', urlM3u)
        xbmc.sleep(500)
        if PY3:
            xbmc.executebuiltin('xbmc.StartPVRManager')
        else:
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "pvr.iptvsimple", "enabled": true }}')
            xbmc.sleep(500)
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "pvr.iptvsimple", "enabled": false }}')
            xbmc.sleep(500)
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "pvr.iptvsimple", "enabled": true }}')
        
        dialog = xbmcgui.Dialog()
        return dialog.ok("Mandrakodi", "PVR configurato correttamente.")
    except Exception as err:
        errMsg="ERRORE: {0}".format(err)
        raise Exception(errMsg)

def reloadDefault():
    home = ''
    if PY3:
        home = xbmcvfs.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
    else:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path').decode('utf-8'))
    defualt_file = os.path.join(home, 'default.py')
    timeUnix=os.path.getmtime(defualt_file)
    logga('TIME FILE '+str(timeUnix))
    if (timeUnix < 1637834000):
        remoteResolverUrl = "https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/default.py"
        strSource = makeRequest(remoteResolverUrl)
        if strSource is None or strSource == "":
            logga('We failed to get source from '+remoteResolverUrl)
            
        else:
            f = open(defualt_file, "w")
            f.write(strSource.encode('utf-8'))
            f.close()
            logga("DEFAULT.PY UPDATE")

def checkJsunpack():
    home = ''
    if PY3:
        home = xbmcvfs.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
    else:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path').decode('utf-8'))
    resolver_file = os.path.join(home, 'jsunpack.py')
    if os.path.exists(resolver_file)==False:
        remoteResolverUrl = "https://mandrakodi.github.io/jsunpack.py"
        strSource = makeRequest(remoteResolverUrl)
        if strSource is None or strSource == "":
            logga('We failed to get source from '+remoteResolverUrl)
            
        else:
            #if PY3:
                #strSource = strSource.decode('utf-8')
            saveFile(resolver_file, strSource)

def checkPortalPy():
    home = ''
    if PY3:
        home = xbmcvfs.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
    else:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path').decode('utf-8'))
    
    resolver_file = os.path.join(home, 'portal_api.py')
    remoteResolverUrl = "https://mandrakodi.github.io/portal_api.py"
    strSource = makeRequest(remoteResolverUrl)
    if strSource is None or strSource == "":
        logga('We failed to get source from '+remoteResolverUrl)
        
    
    if os.path.exists(resolver_file)==False:
        logga("UPDATE PORTAL_API")
        saveFile(resolver_file, strSource)
    else:
        resF = open(resolver_file)
        resolver_content = resF.read()
        resF.close()
        try:
            local_vers = re.findall("versione='(.*)'",resolver_content)[0]
            logga('local_vers '+local_vers)
            remote_vers = re.findall("versione='(.*)'",strSource)[0]
            if local_vers != remote_vers:
                logga("UPDATE PORTAL_API")
                saveFile(resolver_file, strSource)
        except Exception as err:
            logga("NO VERSION - UPDATE PORTAL_API")
            saveFile(resolver_file, strSource)

       

def checkResolver():
    logga("START CHECK_RESOLVER")
    home = ''
    if PY3:
        home = xbmcvfs.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
    else:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path').decode('utf-8'))
    resolver_file = os.path.join(home, 'myResolver.py')
    local_vers = '0.0.0'
    if os.path.exists(resolver_file)==True:
        resF = open(resolver_file)
        resolver_content = resF.read()
        resF.close()
        try:
            local_vers = re.findall("versione='(.*)'",resolver_content)[0]
        except:
            logga('ERRORE FIND LOCAL VERS')
            pass
        logga('Resolver_local_vers '+local_vers)
        
        remoteResolverUrl = "https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/myResolver.py"
        strSource = makeRequest(remoteResolverUrl)
        if strSource is None or strSource == "":
            logga('We failed to get source from '+remoteResolverUrl)
            remote_vers = local_vers
        else:
            #if PY3:
                #strSource = strSource.decode('utf-8')		
            remote_vers = re.findall("versione='(.*)'",strSource)[0]
        logga('remote_vers '+remote_vers)
        if local_vers != remote_vers:
            logga('TRY TO UPDATE VERSION')
            f = open(resolver_file, "w")
            f.write(strSource)
            f.close()
            msgBox("Codice Resolver aggiornato alla versione: "+remote_vers)
            logga('VERSION UPDATE')

def getIPAddress():
    import socket
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "0.0.0.0"

def checkDns():
    import time, requests
    ip = getIPAddress()
    dns1 = "0.0.0.0"
    dns2 = "0.0.0.0"
    gate = "0.0.0.0"
    try:
        dns1 = xbmc.getInfoLabel('Network.DNS1Address')
        dns2 = xbmc.getInfoLabel('Network.DNS2Address')
        gate = xbmc.getInfoLabel('Network.GatewayAddress')
    except:
        pass
    time.sleep(2)
    
    responseCode=404
    try:
        currSess = requests.Session()
        head={'user-agent':'iPad','Content-Type':'application/x-www-form-urlencoded','Referer':'https://daddyhd.com/'}
        page_data1 = currSess.get("https://daddyhd.com/embed/stream-860.php",headers=head)
        responseCode=page_data1.status_code
        dns1 = xbmc.getInfoLabel('Network.DNS1Address')
        dns2 = xbmc.getInfoLabel('Network.DNS2Address')
        gate = xbmc.getInfoLabel('Network.GatewayAddress')
    except:
        pass

    infoDns = "##MANDRA_DNS: "+str(responseCode)
    infoDns += "\n## IP: %s" %  (ip)
    infoDns += "\n## GATE: %s" %  (gate)
    infoDns += "\n## DNS1: %s" %  (dns1)
    infoDns += "\n## DNS2: %s" %  (dns2)
    
    logga("############ START NETWORK INFO ############")
    logga(infoDns)
    logga("############# END NETWORK INFO #############")
    
    if responseCode != 200:
        mess = "Con le attuali impostazioni di rete,\npotresti avere problemi a recuperare i link da alcuni siti \n(es. https://daddyhd.com/)."
        msgBox(mess)

def checkMandraScript():
    have_mandra_plugin = '"enabled":true' in xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","id":1,"params":{"addonid":"script.mandra.kodi", "properties": ["enabled"]}}')
    if have_mandra_plugin == False:
        dialog = xbmcgui.Dialog()
        mess = "Il plugin script.mandra.kodi non risulta installato.\nAlcune funzionalita' non saranno disponibili."
        return dialog.ok("Mandrakodi", mess)

def checkPluginInstalled(pluginId):
    
    have_mandra_plugin = '"enabled":true' in xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","id":1,"params":{"addonid":"'+pluginId+'", "properties": ["enabled"]}}')
    if have_mandra_plugin == False:
        dialog = xbmcgui.Dialog()
        mess = "Il plugin "+pluginId+" non risulta installato."
        dialog.ok("Mandrakodi", mess)
    logga("CHECK IF "+pluginId+" IS INSTALLED: "+str(have_mandra_plugin))
    return have_mandra_plugin
    

def checkMsgOnLog():
    LOGPATH = ''
    if PY3:
        LOGPATH = xbmcvfs.translatePath('special://logpath')
    else:
        LOGPATH = xbmc.translatePath('special://logpath')
    
    log_file = os.path.join(LOGPATH, 'kodi.log')
    if os.path.exists(log_file)==True:
        try:
            logF = open(log_file)
            log_content = logF.read()
            logF.close()
            log_msg = re.findall("MANDRA_DNS",log_content)
            if (log_msg):
                return False
            else:
                return True
        except:
            return True

def uploadLog():
    addon_log_uploader = None
    try:
        addon_log_uploader = xbmcaddon.Addon('script.kodi.loguploader')
    except:
        logga('loguploader seems to be not installed or disabled')
        
        
    if not addon_log_uploader:
        xbmc.executebuiltin('InstallAddon(script.kodi.loguploader)', wait=True)
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "script.kodi.loguploader", "enabled": true }}')
        try:
            addon_log_uploader = xbmcaddon.Addon('script.kodi.loguploader')
        except:
            logga('Logfile Uploader cannot be found')
            
    if not addon_log_uploader:
        logga('Cannot send log because Logfile Uploader cannot be found')
        msgBox("Il plugin Kodi File Uploader non risulta installato. Lo trovi nella repo di Kodi sotto Addon-Programmi.")
        return False
    xbmc.executebuiltin('RunScript(script.kodi.loguploader)')
    return True

def updateCode(parIn):
    home = ''
    if PY3:
        home = xbmcvfs.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
    else:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path').decode('utf-8'))
    launcher_file = os.path.join(home, 'launcher.py')
    if os.path.exists(launcher_file)==True:
        local_vers = "1.0.0"
        try:
            resF = open(launcher_file)
            resolver_content = resF.read()
            resF.close()
            local_vers = re.findall("versione='(.*)'",resolver_content)[0]
        except:
            msgBox("Non e' stato possibile leggere il file locale:[CR]"+launcher_file)
        
        logga('local_vers '+local_vers)


        remoteLauncherUrl = "https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/launcher.py"
        strSource = makeRequest(remoteLauncherUrl)
        if strSource is None or strSource == "":
            logga('We failed to get source from '+remoteLauncherUrl)
            msgBox("Non e' stato possibile contattare la sorgente.[CR]L'addon potrebbe non essere aggiornato.")
            remote_vers = local_vers
        else:
            remote_vers = re.findall("versione='(.*)'",strSource)[0]
        logga('remote_vers '+remote_vers)
        if local_vers != remote_vers:
            logga('TRY TO UPDATE VERSION')
            try:
                f = open(launcher_file, "w")
                f.write(strSource)
                f.close()
                logga('VERSION UPDATE')
                msgBox("Codice Launcher aggiornato alla versione: "+remote_vers)
            except:
                msgBox("Non e' stato possibile aggiornare il file locale:[CR]"+launcher_file)
        else:
            msgBox("Il codice Launcher e' gia' aggiornato all'ultima versione: "+remote_vers)
    else:
        msgBox("Il file launcher.py non e' stato trovato")

    resolve_file = os.path.join(home, 'myResolver.py')
    if os.path.exists(resolve_file)==True:
        local_vers = "1.0.0"
        try:
            resF = open(resolve_file)
            resolver_content = resF.read()
            resF.close()
            local_vers = re.findall("versione='(.*)'",resolver_content)[0]
        except:
            msgBox("Non e' stato possibile leggere il file locale:[CR]"+resolve_file)
        logga('local_vers '+local_vers)


        remoteLauncherUrl = "https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/myResolver.py"
        strSource = makeRequest(remoteLauncherUrl)
        if strSource is None or strSource == "":
            logga('We failed to get source from '+remoteLauncherUrl)
            msgBox("Non e' stato possibile contattare la sorgente.[CR]L'addon potrebbe non essere aggiornato.")
            remote_vers = local_vers
        else:
            remote_vers = re.findall("versione='(.*)'",strSource)[0]
        logga('remote_vers '+remote_vers)
        if local_vers != remote_vers:
            logga('TRY TO UPDATE VERSION')
            try:
                f = open(resolve_file, "w")
                f.write(strSource)
                f.close()
                logga('VERSION UPDATE')
                msgBox("Codice Resolver aggiornato alla versione: "+remote_vers)
            except:
                msgBox("Non e' stato possibile aggiornare il file locale:[CR]"+resolve_file)
        else:
            msgBox("Il codice Resolver e' gia' aggiornato all'ultima versione: "+remote_vers)
    else:
        msgBox("Il file myResolver.py non e' stato trovato")

def copyPlayerCoreFactory(parIn):
    XMLPATH = ''
    if PY3:
        XMLPATH = xbmcvfs.translatePath('special://profile')
    else:
        XMLPATH = xbmc.translatePath('special://profile')
    
    xml_file = os.path.join(XMLPATH, 'playercorefactory.xml')
    dialog = xbmcgui.Dialog()
    if (xbmc.getCondVisibility("system.platform.android")):
        remoteXmlUrl = "https://mandrakodi.github.io/pcf.xml"
        if parIn == "ACETV":
            remoteXmlUrl = "https://mandrakodi.github.io/pcf_tv.xml"
        if parIn == "ACELIVE":
            remoteXmlUrl = "https://mandrakodi.github.io/pcf_live.xml"
        if parIn == "ACEWEB":
            remoteXmlUrl = "https://mandrakodi.github.io/pcf_web.xml"
        if parIn == "ACEATV":
            remoteXmlUrl = "https://mandrakodi.github.io/pcf_atv.xml"
        if parIn == "ACEFREE":
            remoteXmlUrl = "https://mandrakodi.github.io/pcf_free.xml"
        strSource = makeRequest(remoteXmlUrl)
        if strSource is None or strSource == "":
            mess = "Impossibile recuperare il file"
            logga('We failed to get source from '+remoteXmlUrl)
        else:
            #if PY3:
                #strSource = strSource.decode('utf-8')
            try:
                mess = "Si vuole sostituire il file playercorefactory.xml?"
                risposta = dialog.yesno("Mandrakodi", mess, nolabel="Annulla", yeslabel="Procedi")
                if risposta:
                    if (saveFile(xml_file, strSource)):
                        mess = "File salvato correttamente.\nChiudere e riaprire Kodi"
                    else:
                        mess = "Impossibile salvare il file"    
            except:
                mess = "Errore nel salvare il file"
    else:
        mess = "Opzione disponibile solo per sistemi Android"
    dialog.ok("Mandrakodi", mess)

def saveFile(fileName, text):
    res=True
    try:
        f = xbmcvfs.File(fileName, 'w')
        f.write(text)
        f.close()
    except:
        import traceback
        traceback.print_exc()
        return False
    return res

def preg_match(data, patron, index=0):
    try:
        matches = re.findall(patron, data, flags=re.DOTALL)
        return matches[index]
    except:
        return ""

def m3u2json(src):
    import re
    m3uSource = makeRequest(src)
    if m3uSource is None or m3uSource == "":
        logga('We failed to get source from '+src)
        msgBox("Errore download m3u")
        return
    else:
        #if PY3:
            #m3uSource = m3uSource.decode('utf-8')		
        logga('OK source')
        
    regex = r'#EXTINF:(.*?),(.*?)$\s(http.*?//.*?)$'	
    matches = re.compile(regex, re.MULTILINE).findall(m3uSource)
    
    
    numIt=0
    arrTmp = [""]
    strLog="";
    try:
        okGroup=False
        for match in matches:
            if numIt>24999:
                break
            strLog=json.dumps(match)
            tt = match[1]
            title = tt.encode('utf-8', 'ignore').decode('utf-8').replace("'", " ").replace("\r", "").replace("\n", "")
            #title = str(match[1]).strip()
            link = match[2].replace("\r", "").replace("\n", "")
            img = ""
            group = ""
            infos = match[0]
            regex2= r'.*?tvg-logo="(.*?)"'
            urlImg=preg_match(infos, regex2)
            if (urlImg == ""):
                img = "https://www.dropbox.com/s/wd2d403175rbvs7/tv_ch.png?dl=1"
            else:
                img = urlImg
           
            regex3 = r'.*?group-title="(.*?)"'
            group = preg_match(infos, regex3)
            if (group == ""):
                group = "VARIOUS"
            try:
                row = group+"@#@"+title+"@#@"+link+"@#@"+img
                okGroup=True
            except:
                row = group.encode('utf-8', 'ignore').decode('utf-8')+"@#@"+title+"@#@"+link+"@#@"+img
                writeFileLog("\n"+row, "a+")
            #logging.warning(row)
            arrTmp.append(row)
            numIt += 1
    except:
        import traceback
        msgBox("Errore nella lettura del file m3u")
        writeFileLog(str(numIt)+"\n"+strLog, "a+")
        traceback.print_exc()
        return 
    logga("FOUND "+str(numIt)+" ROWS")

    if (okGroup):
        arrTmp.sort()
        
    try:
        strJson = '{"SetViewMode": "503","channels": ['
        oldGroup = ""
        numGoup = 0
        numIt=0
        numLoop=0
        for rowTmp in arrTmp:
            if (rowTmp != ""):
                strLog=rowTmp
                arrRow = rowTmp.split("@#@")
                group = arrRow[0]
                if (oldGroup != group):
                    oldGroup = group
                    if (numGoup > 0):
                        strJson += ']},'
                    strJson += '{'
                    strJson += '"name": "[COLOR lime]'+group+'[/COLOR]",'
                    strJson += '"thumbnail": "https://www.dropbox.com/s/3j4wf8b67xt8gry/fold_tube.png?dl=1",'
                    strJson += '"fanart": "https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
                    strJson += '"info": "[COLOR lime]Category: '+group+'[/COLOR]",'
                    strJson += '"SetViewMode": "503","items":['
                    numGoup += 1
                    numIt=0
                
                strJsonNew = '{'
                strJsonNew += '"title":"'+arrRow[1]+'",'
                strJsonNew += '"thumbnail":"'+arrRow[3]+'",'
                strJsonNew += '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
                link = arrRow[2]
                if link.endswith(".m3u"):
                    strJsonNew += '"m3u":"'+link+'",'
                else:
                    strJsonNew += '"link":"'+link+'",'
                strJsonNew += '"info":"NO INFO"'
                strJsonNew += '}'

                try:
                    json.loads(strJsonNew)
                    if (numIt > 0):
                        strJson += ','
                    strJson +=  strJsonNew
                    numIt += 1
                except:
                    logga("BAD ITEMS: "+strJsonNew)
                    pass
                

        strJson += ']}]}'

        logging.warning("END M3U2JSON. CALL jsonToItems")
        jsonToItems(strJson)
    except:
        import traceback
        msgBox("Errore nella creazione del json")
        writeFileLog(strLog, "w+")
        traceback.print_exc()
        return


def decodeSkinViewMode (mySkin='', viewMode=''):
    retMode=viewMode
    if (retMode == "500" or retMode == "Wall"):
        retMode = str(xbmcaddon.Addon(id=addon_id).getSetting("SkinWall"))
    if (retMode == "50" or retMode == "List1"):
        retMode = str(xbmcaddon.Addon(id=addon_id).getSetting("SkinList1"))
    if (retMode == "51" or retMode == "List2"):
        retMode = str(xbmcaddon.Addon(id=addon_id).getSetting("SkinList2"))
    if (retMode == "503" or retMode == "Info1"):
        retMode = str(xbmcaddon.Addon(id=addon_id).getSetting("SkinInfo1"))
    if (retMode == "504" or retMode == "Info2"):
        retMode = str(xbmcaddon.Addon(id=addon_id).getSetting("SkinInfo2"))
    logga ("SKIN: "+mySkin+" - VIEW: "+str(retMode))

    return retMode

def personalList(listtType=''):
    import json
    baseScript = makeRequest("https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/data/enterScrip.txt")
    if baseScript is None or baseScript == "":
        logga('We failed to get source from serverSource')
        
    else:
        #if PY3:
            #baseScript = baseScript.decode('utf-8')
        logga('OK get source from serverSource')
        
    baseScript = baseScript.replace("\r\n", "").replace("\n", "").replace("\r", "")          
    urlToCall=""
    fileName=""
    if 	(listtType=="MAC"):
        fileName = xbmcaddon.Addon(id=addon_id).getSetting("macFile")
    if 	(listtType=="IPTV"):
        fileName = xbmcaddon.Addon(id=addon_id).getSetting("iptvFile")
    if 	(listtType=="M3U"):
        fileName = xbmcaddon.Addon(id=addon_id).getSetting("m3uFile")

    if (fileName=="" or fileName=="blank"):
        msgBox("E' necessario specificare un file nelle impostazioni")
    else:
        logga('FILE_NAME: '+fileName)
        urlToCall=baseScript+"JOB810&type="+listtType+"&url="+fileName
        if 	(listtType=="MAC"):
            urlToCall=baseScript+"JOB811&url="+fileName
        logga('URL TO CALL: '+urlToCall)
        try:
            return getExternalJson(urlToCall)
        except Exception as err:
            msgBox("Non e' stato possibile leggere i dati. Controllare se il file e' presente")
            remoteLog(personalList+"@@"+urlToCall)


def checkSkin():
    kodiSkin=xbmc.getSkinDir()
    wall=xbmcaddon.Addon(id=addon_id).getSetting("SkinWall")
    if str(kodiSkin).endswith("estuary"):
        logga ("SKIN ESTUARY")
        if (wall!="55"):
            xbmcaddon.Addon(id=addon_id).setSetting("SkinWall", "55")    
            xbmcaddon.Addon(id=addon_id).setSetting("SkinList1", "55")    
            xbmcaddon.Addon(id=addon_id).setSetting("SkinList2", "55")    
            xbmcaddon.Addon(id=addon_id).setSetting("SkinInfo1", "55")    
            xbmcaddon.Addon(id=addon_id).setSetting("SkinInfo2", "55")    
    if str(kodiSkin).endswith("confluence"):
        logga ("SKIN CONFLUENCE")
        if (wall!="500"):
            dialog = xbmcgui.Dialog()
            mess="Rilevata Skin Confluence. Vuoi impostare la visualizzazione per questa skin?"
            resp= dialog.yesno("MandraKodi", mess)
            if (resp):
                xbmcaddon.Addon(id=addon_id).setSetting("SkinWall", "500")    
                xbmcaddon.Addon(id=addon_id).setSetting("SkinList1", "50")    
                xbmcaddon.Addon(id=addon_id).setSetting("SkinList2", "51")    
                xbmcaddon.Addon(id=addon_id).setSetting("SkinInfo1", "503")    
                xbmcaddon.Addon(id=addon_id).setSetting("SkinInfo2", "504")
                msgBox("Visualizzazione impostata")    


def msgBox(mess):
    dialog = xbmcgui.Dialog()
    dialog.ok("MandraKodi", mess)

def remoteLog(msgToLog):
    if PY3:
        import urllib.parse as myParse
    else:
        import urllib as myParse
    
    
    baseLog = "https://test34344.herokuapp.com/filter.php?numTest=JOB999"
    urlLog = baseLog + "&msgLog=" + myParse.quote(ua+"@@"+msgToLog)
    strSource = makeRequest(urlLog)
    if strSource is None or strSource == "":
        logga('MANDRA_LOG: NO REMOTE LOG')
        
    else:
        logga('OK REMOTE LOG')
        

def writeFileLog(strIn, modo):
    home = ''
    if PY3:
        home = xbmcvfs.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
        log_file = os.path.join(home, 'mandrakodi2.log')
        f = open(log_file, modo, encoding="utf-8")
        f.write(strIn)
        f.close()
    else:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path').decode('utf-8'))
        log_file = os.path.join(home, 'mandrakodi2.log')
        f = open(log_file, modo)
        f.write(strIn)
        f.close()

def deleteSettings(parIn):
    XMLPATH = ''
    if PY3:
        XMLPATH = xbmcvfs.translatePath('special://profile')
    else:
        XMLPATH = xbmc.translatePath('special://profile')
    
    xml_file = os.path.join(XMLPATH, 'addon_data/plugin.video.mandrakodi/settings.xml')
    if os.path.exists(xml_file):
        dialog = xbmcgui.Dialog()
        mess="Vuoi davvero resettare il file settings.xml?"
        resp= dialog.yesno("MandraKodi", mess)
        if (resp):
            os.remove(xml_file)
            msgBox("File settings resettato.\nChiudi l'addon e metti i parametri nelle impostazioni.")
    else:
        msgBox("File settings non presente")

def run():
    action = "start"
    url = "start"
    try:
        if not sys.argv[2]:
            logga("=== ADDON START ===")
            if (checkMsgOnLog()):
                checkResolver()
                checkJsunpack()
                checkPortalPy()
                checkDns()
                #checkMandraScript()
            checkSkin()
            getSource()
        else:
            params = parameters_string_to_dict(sys.argv[2])
            action =  params['action']
            url =  params['url']
            
            if action == 'getExtData':
                getExternalJson(url)
            elif action == 'getExtData2':
                clipB=""
                keyboard = xbmc.Keyboard(clipB,'Inserisci Valore')
                keyboard.doModal()
                if not (keyboard.isConfirmed() == False):
                    userInput = keyboard.getText().replace(" ", "+")
                    if not (userInput == ''):
                        if PY3:
                            import urllib.parse as myParse
                        else:
                            import urllib as myParse

                        logging.warning("GET JSON FROM: "+userInput)
                        #strUrl = url + userInput.replace(" ", "+")
                        strUrl = url + myParse.quote(userInput)
                        logging.warning("GET JSON FROM: "+strUrl)
                        getExternalJson(strUrl)
                    else:
                        logga("NO INPUT")
                        mesNoInput='{"SetViewMode":"500","items":[{"title":"[COLOR red]NO INPUT[/COLOR]","link":"ignore","thumbnail":"https://e7.pngegg.com/pngimages/56/148/png-clipart-computer-icons-wrong-miscellaneous-blue-thumbnail.png","fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg","info":"NO INPUT"}]}'
                        jsonToItems(mesNoInput)
                else:
                    logga("EXIT KEYBOARD")
                    mesNoInput='{"SetViewMode":"500","items":[{"title":"[COLOR red]NO INPUT[/COLOR]","link":"ignore","thumbnail":"https://e7.pngegg.com/pngimages/56/148/png-clipart-computer-icons-wrong-miscellaneous-blue-thumbnail.png","fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg","info":"NO INPUT"}]}'
                    jsonToItems(mesNoInput)
            elif action == 'apk':
                apkN =  params['apk']
                logga("RUN APK: "+apkN)
                runApk(apkN, url)
            elif action == 'getChannel':
                logga("OPEN CHANNEL: "+url)
                channelToItems(url, _handle)
            elif action == 'personal':
                logga("OPEN PERSONAL: "+url)
                personalList(url)
            elif action == 'regex':
                express =  params['exp']
                logga("REGEX: "+url+" - "+express)
                url = simpleRegex(url, express)
                play_video(url)
            elif action == 'myresolve':
                parIn =  params['parIn']
                logga("MyResolver: "+url+" - "+parIn)
                callReolver(url, parIn)
            elif action == 'openSettings':
                try:
                    xbmcaddon.Addon().openSettings()
                    xbmcgui.Dialog().ok('[B][COLOR yellow]AVVISO[/COLOR][/B]','[COLOR lime]CHIUDI KODI E APRI DI NUOVO PER AGGIORNARE IMPOSTAZIONI[/COLOR]')
                    xbmc.executebuiltin("XBMC.Container.Refresh()")
                except:
                    xbmc.executebuiltin('Addon.OpenSettings(plugin.video.mandrakodi)')
            elif action == 'plugin':
                logga("CALL PLUGIN: "+url)
                url2=url.replace("plugin://", "")
                url3=url2.split("?")
                pl=""
                par=""
                if ('?' in url):
                    pl=url3[0].replace("/", "")
                    par=url3[1]
                    logga("plug: "+pl+" --> "+par)
                    if (checkPluginInstalled(pl)):
                        xbmc.executebuiltin("RunPlugin("+url+")")
                else:
                    pl=url3[0].replace("/", "")
                    logga("onlyplugin: "+pl)
                    if (checkPluginInstalled(pl)):
                        xbmc.executebuiltin('RunAddon("'+pl+'")')

            elif action == 'play':
                if url.startswith("acestream"):
                    dialog = xbmcgui.Dialog()
                    options = ["ENGINE", "DIRETTO", "HORUS"]
                    resp = dialog.select("Seleziona meodo di riproduzione", options)
                    #mess="Vuoi usare l'engine per il link ace?"
                    #resp= dialog.yesno("MandraKodi", mess)
                    if (resp==0):
                        baseAce="http://127.0.0.1:6878"
                        try:
                            setAce=xbmcaddon.Addon(id=addon_id).getSetting("urlAppo3")
                            if (setAce[0:4]=="http"):
                                baseAce=setAce
                        except:
                            pass
                        uArr = url.split("/")
                        url=baseAce+"/ace/getstream?id="+uArr[-1]
                        logga("URL_ACE: "+url)
                    elif (resp==1):
                        if (xbmc.getCondVisibility("system.platform.android")):
                            options2 = ["PlayerCoreFactory", "org.acestream.media", "org.acestream.media.atv", "org.acestream.core", "org.acestream.core.atv", "org.acestream.node", "org.acestream.web", "org.free.aceserve"]
                            resp2 = dialog.select("Seleziona nome APK", options2)
                            if (resp2 > 0):
                                apkAce=options2[resp2]
                                runApk(apkAce, url)
                    elif (resp==2):
                        uArr = url.split("/")
                        url="plugin://script.module.horus?action=play&title=by%20MandraKodi&id="+uArr[-1]
                    elif (resp==-1):
                        url=""
                play_video(url)
            elif action == 'm3u':
                m3u2json(url)
            elif action == 'pvr':
                setPvr(url)
            elif action == 'log':
                uploadLog()
            elif action == 'copyXml':
                copyPlayerCoreFactory(url)
            elif action == 'updateCode':
                updateCode(url)
            elif action == 'delSet':
                deleteSettings(url)
            else:
                raise Exception('Invalid paramstring: {0}!'.format(params))
    except Exception as err:
        import traceback
        
        errMsg="ERROR_MK2: {0}".format(err)
        par=re.split('%3f', sys.argv[2])
        parErr = par[-1]
        logging.warning(errMsg+"\nPAR_ERR --> "+parErr)
        errToLog = action + "@@" + url
        remoteLog(errToLog)
        traceback.print_exc()
        raise err

    if not viewmode==None and autoView=="1":
        time.sleep(0.5)
        logga("setting viewmode")
        kodiSkin=xbmc.getSkinDir()
        kodiView=decodeSkinViewMode(kodiSkin, viewmode)
        xbmc.executebuiltin("Container.SetViewMode("+kodiView+")")
        time.sleep(0.5)
        logga("setting view mode again to "+kodiView)
        xbmc.executebuiltin("Container.SetViewMode("+kodiView+")")
        xbmcaddon.Addon(id=addon_id).setSetting("urlAppo1", kodiView)
        logga("Last ViewMode Saved: "+kodiView)
    if debug == "on":
        logging.warning("MANDRA_LOG: \n"+testoLog)
        
