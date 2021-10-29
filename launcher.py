versione='1.0.48'
# Module: launcher
# Author: ElSupremo
# Created on: 22.02.2021
# Last update: 29.10.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
import logging
import xbmcgui
import xbmc
import os
import xbmcplugin
import xbmcaddon
import json
import re
import xbmcvfs

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
addon_id = 'plugin.video.mandrakodi'
selfAddon = xbmcaddon.Addon(id=addon_id)
selfAddon.setSetting("debug", "on")
debug = selfAddon.getSetting("debug")
showAdult = selfAddon.getSetting("ShowAdult")
testoLog = "";
viewmode="51"

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
		
def makeRequest(url, hdr=None):
    logga('Try to open '+url)
    html = ""
    if PY3:
	    import urllib.request as myRequest
    else:
	    import urllib2 as myRequest
    pwd = selfAddon.getSetting("password")
    version = selfAddon.getAddonInfo("version")
    if hdr is None:
        ua = "MandraKodi2@@"+version+"@@"+pwd
        hdr = {"User-Agent" : ua}
    try:
        req = myRequest.Request(url, headers=hdr)
        response = myRequest.urlopen(req, timeout=45)
        html = response.read().decode('utf-8')
        response.close()
    except:
        logging.warning('Error to open url: '+url)
        pass
    return html

def getSource():
    #startUrl = "https://mandrakodi.github.io/data/disclaimer.json"
    startUrl = "https://www.dropbox.com/s/igyq58cnpjq0fq4/disclaimer.json?dl=1"
    try:
        strSource = makeRequest(startUrl)
        if strSource is None or strSource == "":
            logging.warning('MANDRA_LOG: NO DISCLAIMER')
            strSource = underMaintMsg()
        else:
            logga('OK SOURCE ')
            liveVersion = "Mandrakodi "+str(selfAddon.getAddonInfo("version"))
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

def play_video(path):
    urlClean=path.replace(" ", "%20")
    play_item = xbmcgui.ListItem(path=urlClean)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def getTxtMessage(vName):
    home = ''
    if PY3:
        home = xbmc.translatePath(selfAddon.getAddonInfo('path'))
    else:
        home = xbmc.translatePath(selfAddon.getAddonInfo('path').decode('utf-8'))
    fPath = os.path.join(home, vName)
    resF = open(fPath)
    file_content = resF.read()
    resF.close()
    return file_content

def getExternalJson(strPath):
    strSource = makeRequest(strPath)
    if (strSource == ""):
        msgBox("Spiacenti, la fonte non e' raggiungibile")
        remoteLog("NO_FONTE@@"+strPath)
        logging.warning("NO JSON AT: "+strPath)
    else:
        jsonToItems(strSource)
	
def jsonToItems(strJson):
    global viewmode
    try:
        dataJson = json.loads(strJson)
    except Exception as err:
        errMsg="Errore: Nessuna risposta dal server (No Json)"
        msgBox(errMsg)
        remoteLog("BAD_JSON")
    
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
        logga('no channels. GetItems')
        pass
    
    link = ""
    try:
        for item in dataJson["items"]:
            titolo = "NO TIT"
            thumb = "https://www.andreisfina.it/wp-content/uploads/2018/12/no_image.jpg"
            fanart = "https://www.andreisfina.it/wp-content/uploads/2018/12/no_image.jpg"
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
                if "@@" in link:
                    arrT=link.split("@@")
                    link=arrT[0]
                    resolverPar=arrT[1]
                elif ":" in link:
                    arrT=link.split(":")
                    link=arrT[0]
                    resolverPar=arrT[1]
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
                is_folder = True
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
            elif is_yatse == True:
                list_item.setProperty('IsPlayable', 'true')
                url = get_urlYatse(action='share', type='unresolvedurl', data=link)
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
        xbmcplugin.endOfDirectory(_handle)
    except:
        msgBox("Errore nella lettura del json")
        remoteLog("NO_JSON_READ@@"+link)
        logging.warning(strJson)


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_urlMagnet(**kwargs):
    return '{0}?{1}'.format("plugin://plugin.video.elementum/play", urlencode(kwargs))

def get_urlChrome(**kwargs):
    return '{0}?{1}'.format("plugin://plugin.program.browser.launcher/", urlencode(kwargs))

def get_urlYatse(**kwargs):
    return '{0}?{1}'.format("plugin://script.mandra.kodi/", urlencode(kwargs))

def parameters_string_to_dict(parameters):
    params = dict(parse_qsl(parameters.split('?')[1]))
    return params

def jsonToChannels(strJson):
    channelsArray = json.loads(strJson)
    window = xbmcgui.Window(10000)
    window.setProperty("chList", strJson)
    xbmcplugin.setContent(_handle, 'movies')
    for channel in channelsArray["channels"]:
        titolo = "NO TIT"
        thumb = "https://www.andreisfina.it/wp-content/uploads/2018/12/no_image.jpg"
        fanart = "https://www.andreisfina.it/wp-content/uploads/2018/12/no_image.jpg"
        genre = "generic"
        info = ""
        link = ""
        if 'name' in channel:
            titolo = channel["name"]
        if 'thumbnail' in channel:
            thumb = channel["thumbnail"]
        if 'fanart' in channel:
            fanart = channel["fanart"]
        if 'info' in channel:
            info = channel["info"]
        list_item = xbmcgui.ListItem(label=titolo)
        list_item.setInfo('video', {'title': titolo,'genre': genre,'plot': info,'mediatype': 'movie','credits': 'ElSupremo'})
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'poster': thumb, 'landscape': fanart, 'fanart': fanart})
        url = get_url(action='getChannel', url=titolo)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)
   
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

def callReolver(metodo, parametro):
    global viewmode
    import myResolver

    retVal = myResolver.run(metodo, parametro)

    xbmcplugin.setContent(_handle, 'movies')
    thumb="https://cdn.pixabay.com/photo/2012/04/12/20/56/play-30619_640.png"
    fanart="https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"
    if isinstance(retVal, list):
        numLink=1
        
        for linkTmp in retVal:
            newList=list(retVal[0])
            newLink=newList[0]
            newP=newList[1]
            info=""
            if len(newList)==3:
                info=newList[2]
                viewmode="503"

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
    xbmcplugin.endOfDirectory(_handle)

def runApk(apkName, apkPar):
    xbmc.executebuiltin('StartAndroidActivity("'+apkName+'", "android.intent.action.VIEW", "", "'+apkPar+'")')

def getPvr():
    myPvr = None
        
    if not os.path.exists(xbmc.translatePath('special://home/addons/pvr.iptvsimple')) and not os.path.exists(xbmc.translatePath('special://xbmcbinaddons/pvr.iptvsimple')):
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

def checkJsunpack():
    home = ''
    if PY3:
        home = xbmc.translatePath(selfAddon.getAddonInfo('path'))
    else:
        home = xbmc.translatePath(selfAddon.getAddonInfo('path').decode('utf-8'))
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
        home = xbmc.translatePath(selfAddon.getAddonInfo('path'))
    else:
        home = xbmc.translatePath(selfAddon.getAddonInfo('path').decode('utf-8'))
    resolver_file = os.path.join(home, 'portal_api.py')
    if os.path.exists(resolver_file)==False:
        remoteResolverUrl = "https://mandrakodi.github.io/portal_api.py"
        strSource = makeRequest(remoteResolverUrl)
        if strSource is None or strSource == "":
            logga('We failed to get source from '+remoteResolverUrl)
        else:
            if PY3:
                strSource = strSource.decode('utf-8')
            saveFile(resolver_file, strSource)

def checkResolver():
    home = ''
    if PY3:
        home = xbmc.translatePath(selfAddon.getAddonInfo('path'))
    else:
        home = xbmc.translatePath(selfAddon.getAddonInfo('path').decode('utf-8'))
    resolver_file = os.path.join(home, 'myResolver.py')
    if os.path.exists(resolver_file)==True:
        resF = open(resolver_file)
        resolver_content = resF.read()
        resF.close()
        local_vers = re.findall("versione='(.*)'",resolver_content)[0]
        logga('local_vers '+local_vers)
        
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

def checkDns():
    ip = xbmc.getIPAddress()
    dns1 = xbmc.getInfoLabel('Network.DNS1Address')
    dns2 = xbmc.getInfoLabel('Network.DNS2Address')
    logging.warning("MANDRA_DNS")
    logga("############ START NETWORK INFO ############")
    logga("## IP: %s" %  (ip))
    logga("## DNS1: %s" %  (dns1))
    logga("## DNS2: %s" %  (dns2))
    logga("############# END NETWORK INFO #############")
    okDns=False
    if dns1 == "1.1.1.1" or dns1 == "8.8.8.8" or dns1 == "192.168.0.1" or dns1 == "127.0.0.1":
        okDns=True
    elif dns1 == "1.0.0.1" or dns1 == "8.8.4.4" or dns1 == "192.168.1.1" or dns1 == "192.168.1.254":
        okDns=True
    elif dns2 == "1.1.1.1" or dns2 == "8.8.8.8" or dns2 == "192.168.0.1" or dns2 == "127.0.0.1":
        okDns=True
    elif dns2 == "1.1.1.1" or dns2 == "8.8.4.4" or dns2 == "192.168.1.1" or dns2 == "192.168.1.254":
        okDns=True
    if okDns == False:
        dialog = xbmcgui.Dialog()
        mess = "Con i DNS attualmente impostati, "+dns1+" - "+dns2+",\npotresti avere problemi a recuperare i link da alcuni siti.\nSe puoi, utilizza quelli di CloudFlare [1.1.1.1 - 1.0.0.1]"
        return dialog.ok("Mandrakodi", mess)

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
    logga("CHECK IF "+pluginId+" IS INSTALLED: "+have_mandra_plugin)
    return have_mandra_plugin
    

def checkMsgOnLog():
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
        logga.info('loguploader seems to be not installed or disabled')
    if not addon_log_uploader:
        xbmc.executebuiltin('InstallAddon(script.kodi.loguploader)', wait=True)
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "script.kodi.loguploader", "enabled": true }}')
        try:
            addon_log_uploader = xbmcaddon.Addon('script.kodi.loguploader')
        except:
            logga.info('Logfile Uploader cannot be found')
    if not addon_log_uploader:
        logga('Cannot send log because Logfile Uploader cannot be found')
        return False
    xbmc.executebuiltin('RunScript(script.kodi.loguploader)')
    return True

def copyPlayerCoreFactory(parIn):
    XMLPATH = xbmc.translatePath('special://profile')
    xml_file = os.path.join(XMLPATH, 'playercorefactory.xml')
    dialog = xbmcgui.Dialog()
    if (xbmc.getCondVisibility("system.platform.android")):
        remoteXmlUrl = "https://mandrakodi.github.io/pcf.xml"
        if parIn == "ACETV":
            remoteXmlUrl = "https://mandrakodi.github.io/pcf_tv.xml"
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
    try:
	    f = xbmcvfs.File(fileName, 'w')
	    f.write(text)
	    f.close()
    except:
	    return False
    return True

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
    else:
        #if PY3:
            #m3uSource = m3uSource.decode('utf-8')		
        logga('OK source')
    regex = r'#EXTINF:(.*?),(.*?)$\s(http.*?//.*?)$'	
    matches = re.compile(regex, re.MULTILINE).findall(m3uSource)
    
    
    numIt=0
    arrTmp = [""]
    for match in matches:
        title = str(match[1]).strip()
        link = str(match[2]).strip()
        img = ""
        group = ""
        infos = str(match[0]).strip()
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
        row = group+"@@"+title+"@@"+link+"@@"+img
        #logging.warning(row)
        arrTmp.append(row)
        numIt += 1
    logga("FOUND "+str(numIt)+" ROWS")

    arrTmp.sort()
    strJson = '{"SetViewMode": "500","channels": ['
    oldGroup = ""
    numGoup = 0
    numIt=0
    numLoop=0
    for rowTmp in arrTmp:
        if (rowTmp != ""):
            arrRow = rowTmp.split("@@")
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
                strJson += '"items":['
                numGoup += 1
                numIt=0
            
            if (numIt > 0):
                strJson += ','
            strJson += '{'
            strJson += '"title":"'+arrRow[1]+'",'
            strJson += '"thumbnail":"'+arrRow[3]+'",'
            strJson += '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            link = arrRow[2]
            if link.endswith(".m3u"):
                strJson += '"m3u":"'+link+'",'
            else:
                strJson += '"link":"'+link+'",'
            strJson += '"info":"NO INFO"'
            strJson += '}'
            numIt += 1

    strJson += ']}]}'

    logging.warning(strJson)
    jsonToItems(strJson)


def decodeSkinViewMode (mySkin='', viewMode=''):
    retMode=viewMode
    if (retMode == "500" or retMode == "Wall"):
        retMode = str(selfAddon.getSetting("SkinWall"))
    if (retMode == "50" or retMode == "List1"):
        retMode = str(selfAddon.getSetting("SkinList1"))
    if (retMode == "51" or retMode == "List2"):
        retMode = str(selfAddon.getSetting("SkinList2"))
    if (retMode == "503" or retMode == "Info1"):
        retMode = str(selfAddon.getSetting("SkinInfo1"))
    if (retMode == "504" or retMode == "Info2"):
        retMode = str(selfAddon.getSetting("SkinInfo2"))
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
        fileName = selfAddon.getSetting("macFile")
    if 	(listtType=="IPTV"):
        fileName = selfAddon.getSetting("iptvFile")
    if 	(listtType=="M3U"):
        fileName = selfAddon.getSetting("m3uFile")

    if (fileName=="" or fileName=="blank"):
        msgBox("E' necessario specificare un file nelle impostazioni")
    else:
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
    wall=selfAddon.getSetting("SkinWall")
    if str(kodiSkin).endswith("estuary"):
        logga ("SKIN ESTUARY")
        if (wall!="55"):
            dialog = xbmcgui.Dialog()
            mess="Rilevata Skin Estuary. Vuoi impostare la visualizzazione per questa skin?"
            resp= dialog.yesno("MandraKodi", mess)
            if (resp):
                selfAddon.setSetting("SkinWall", "55")    
                selfAddon.setSetting("SkinList1", "55")    
                selfAddon.setSetting("SkinList2", "55")    
                selfAddon.setSetting("SkinInfo1", "55")    
                selfAddon.setSetting("SkinInfo2", "55")
                msgBox("Visualizzazione impostata")    
    if str(kodiSkin).endswith("confluence"):
        logga ("SKIN CONFLUENCE")
        if (wall!="500"):
            dialog = xbmcgui.Dialog()
            mess="Rilevata Skin Confluence. Vuoi impostare la visualizzazione per questa skin?"
            resp= dialog.yesno("MandraKodi", mess)
            if (resp):
                selfAddon.setSetting("SkinWall", "500")    
                selfAddon.setSetting("SkinList1", "50")    
                selfAddon.setSetting("SkinList2", "51")    
                selfAddon.setSetting("SkinInfo1", "503")    
                selfAddon.setSetting("SkinInfo2", "504")
                msgBox("Visualizzazione impostata")    


def msgBox(mess):
    dialog = xbmcgui.Dialog()
    dialog.ok("MandraKodi", mess)

def remoteLog(msgToLog):
    baseLog = "http://test34344.herokuapp.com/filter.php?numTest=JOB999"
    urlLog = baseLog + "&msgLog=" + msgToLog
    strSource = makeRequest(urlLog)
    if strSource is None or strSource == "":
        logga('MANDRA_LOG: NO REMOTE LOG')
    else:
        logga('OK REMOTE LOG')

def run():
    action = "start"
    url = "start"
    try:
        if not sys.argv[2]:
            logga("=== ADDON START ===")
            checkResolver()
            checkJsunpack()
            checkPortalPy()
            if (checkMsgOnLog()):
                checkDns()
                checkMandraScript()
                checkSkin()
            getSource()
        else:
            params = parameters_string_to_dict(sys.argv[2])
            action =  params['action']
            url =  params['url']
            logga("ACTION ==> "+action)
            logga("URL ==> "+url)
            if action == 'getExtData':
                getExternalJson(url)
            elif action == 'getExtData2':
                clipB=""
                keyboard = xbmc.Keyboard(clipB,'Inserisci Valore')
                keyboard.doModal()
                if not (keyboard.isConfirmed() == False):
                    userInput = keyboard.getText()
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
                logga("OPEN CHANNEL: "+url)
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
                xbmcaddon.Addon().openSettings()
                xbmcgui.Dialog().ok('[B][COLOR yellow]AVVISO[/COLOR][/B]','[COLOR lime]CHIUDI KODI E APRI DI NUOVO PER AGGIORNARE IMPOSTAZIONI[/COLOR]')
                xbmc.executebuiltin("XBMC.Container.Refresh()")
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
                play_video(url)
            elif action == 'm3u':
                m3u2json(url)
            elif action == 'pvr':
                setPvr(url)
            elif action == 'log':
                uploadLog()
            elif action == 'copyXml':
                copyPlayerCoreFactory(url)
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

    if not viewmode==None:
        logga("setting viewmode")
        kodiSkin=xbmc.getSkinDir()
        kodiView=decodeSkinViewMode(kodiSkin, viewmode)
        xbmc.executebuiltin("Container.SetViewMode("+kodiView+")")
        logga("setting view mode again to "+kodiView)
        xbmc.executebuiltin("Container.SetViewMode("+kodiView+")")
    if debug == "on":
        logging.warning("MANDRA_LOG: \n"+testoLog)
