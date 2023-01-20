versione='1.1.49'
# Module: myResolve
# Author: ElSupremo
# Created on: 10.04.2021
# Last update: 20.01.2023
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import re, requests, sys, logging, uuid
import xbmcgui
import xbmc
import xbmcaddon
import os
import string
import random


addon_id = 'plugin.video.mandrakodi'
#selfAddon = xbmcaddon.Addon(id=addon_id)
debug = xbmcaddon.Addon(id=addon_id).getSetting("debug")

PY3 = sys.version_info[0] == 3
if PY3:
    import urllib.parse as myParse
    import xbmcvfs
else:
    import urllib as myParse

def logga(mess):
    if debug == "on":
        logging.warning("MANDRA_RESOLVE: "+mess)

def rocktalk(parIn=None):
    from base64 import b64encode, b64decode
    from binascii import a2b_hex
    from Cryptodome.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
    from Cryptodome.Cipher import DES
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Util.Padding import unpad

    user_agent = 'USER-AGENT-tvtap-APP-V2'
    headers = {
        'User-Agent': user_agent,
        'app-token': '37a6259cc0c1dae299a7866489dff0bd',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'taptube.net',
	}

    _pubkey2 = RSA.importKey(
        a2b_hex(
            "30819f300d06092a864886f70d010101050003818d003081890281"
            "8100bfa5514aa0550688ffde568fd95ac9130fcdd8825bdecc46f1"
            "8f6c6b440c3685cc52ca03111509e262dba482d80e977a938493ae"
            "aa716818efe41b84e71a0d84cc64ad902e46dbea2ec61071958826"
            "4093e20afc589685c08f2d2ae70310b92c04f9b4c27d79c8b5dbb9"
            "bd8f2003ab6a251d25f40df08b1c1588a4380a1ce8030203010001"
        )
    )

    _msg2 = a2b_hex(
        "7b224d4435223a22695757786f45684237686167747948392b58563052513d3d5c6e222c22534"
        "84131223a2242577761737941713841327678435c2f5450594a74434a4a544a66593d5c6e227d"
    )

    cipher = Cipher_PKCS1_v1_5.new(_pubkey2)	
    tkn2 =  b64encode(cipher.encrypt(_msg2))
    ch_id = parIn
    r2 = requests.post('https://rocktalk.net/tv/index.php?case=get_channel_link_with_token_latest', 
        headers={"app-token": "37a6259cc0c1dae299a7866489dff0bd"},
        data={"payload": tkn2, "channel_id": ch_id, "username": "603803577"},
        timeout=15)

    logga('JSON TVTAP: '+str(r2.json()))

    from pyDes import des, PAD_PKCS5
    key = b"98221122"

    links = []
    linksTmp = []
    jch = r2.json()["msg"]["channel"][0]
    chName=jch["channel_name"]
    chCountry=jch["country"]
    chImg="https://rocktalk.net/tv/"+jch["img"]
    chTit="[COLOR lime]"+chName+"[/COLOR] [COLOR aqua]("+chCountry+")[/COLOR]"

    for stream in jch.keys():
        if "stream" in stream or "chrome_cast" in stream:
            d = des(key)
            link = d.decrypt(b64decode(jch[stream]), padmode=PAD_PKCS5)
            if link:
                link = link.decode("utf-8")
                if not link == "dummytext" and link not in linksTmp:
                    links.append((link, chTit, stream, chImg))
                    linksTmp.append(link)

    return links


def myStream(parIn=None):
    video_urls = []
    page_url = "https://embed.mystream.to/"+parIn
    logga('CALL: '+page_url)
    page_data = requests.get(page_url,headers={'user-agent':'Mozilla/5.0','accept':'*/*'}).content
    if PY3:
        page_data = page_data.decode('utf-8')

    page_decode = decodeMyStream(page_data)
    video_url = preg_match(page_decode, r"'src',\s*'([^']+)")

    logga('video_url '+video_url)
    video_urls.append((video_url, ""))

    return video_urls


def decodeMyStream(data):
    # adapted from MyStream.py code - https://github.com/kodiondemand/addon/blob/master/servers/mystream.py
    first_group = preg_match(data, r'"\\"("\+.*?)"\\""\)\(\)\)\(\)')
    match = preg_match(first_group, r"(\(!\[\]\+\"\"\)\[.+?\]\+)")
    if match:
        first_group = first_group.replace(match, 'l').replace('$.__+', 't').replace('$._+', 'u').replace('$._$+', 'o')

        tmplist = []

        js = preg_match(data, r'(\$={.+?});')
        if js:
            js_group = js[3:][:-1]
            second_group = js_group.split(',')

            i = -1
            for x in second_group:
                a, b = x.split(':')

                if b == '++$':
                    i += 1
                    tmplist.append(("$.{}+".format(a), i))

                elif b == '(![]+"")[$]':
                    tmplist.append(("$.{}+".format(a), 'false'[i]))

                elif b == '({}+"")[$]':
                    tmplist.append(("$.{}+".format(a), '[object Object]'[i]))

                elif b == '($[$]+"")[$]':
                    tmplist.append(("$.{}+".format(a), 'undefined'[i]))

                elif b == '(!""+"")[$]':
                    tmplist.append(("$.{}+".format(a), 'true'[i]))

            tmplist = sorted(tmplist, key=lambda z: str(z[1]))
            for x in tmplist:
                first_group = first_group.replace(x[0], str(x[1]))

            first_group = first_group.replace('\\"', '\\').replace("\"\\\\\\\\\"", "\\\\").replace('\\"', '\\').replace('"', '').replace("+", "")

    return first_group.encode('ascii').decode('unicode-escape').encode('ascii').decode('unicode-escape')

def wizhdFind(parIn):
    logga('CALL: '+parIn)
    page_data = requests.get(parIn,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':'http://wizhdsports.net/'}).content
    if PY3:
        page_data = page_data.decode('utf-8')

    iframe_url = preg_match(page_data, r'iframe\s*src="([^"]+)')
    logga('IFRAME WIZ: '+iframe_url)

    vUrl = findM3u8(iframe_url, parIn)
    return vUrl

def wizhd(parIn=None):
    video_urls = []
    if parIn.startswith('http'):
        page_url = parIn
    else:
        page_url = "http://wizhdsports.net/"+parIn
    
    vUrl = wizhdFind(page_url)
    video_urls.append((vUrl, ""))
    if "|" in vUrl:
        arrV = vUrl.split("|")
        video_urls.append((arrV[0], ""))		

    return video_urls
    

def findM3u8(linkIframe, refPage):
    #logging.warning('URL: '+linkIframe)
    vUrl = ""
    try:
        page_data2 = requests.get(linkIframe,headers={'user-agent':'iPad','accept':'*/*','referer':refPage}).content

        if PY3:
            page_data2 = page_data2.decode('utf-8')

        video_url = preg_match(page_data2, r'source:\s*"([^"]+)')
        if video_url == "":
            video_url = preg_match(page_data2, r"source:\s*'([^']+)")
        if video_url != "":
            vUrl = video_url + '|User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F74.0.3729.169+Safari%2F537.36&Referer='+linkIframe
        logga('video_url '+vUrl)

    except:
        pass

    return vUrl

def assiaFind(parIn):
    logga('ASSIA_PAR: '+parIn)
    video_url = findM3u8(parIn, 'http://assia1.tv/')
    logga('video_url '+video_url)
    return video_url

def assia(parIn=None):
    video_urls = []
    video_url = assiaFind(parIn)
    video_urls.append((video_url, ""))
    if "|" in video_url:
        arrV = video_url.split("|")
        video_urls.append((arrV[0], ""))		
    return video_urls

def daddyFind(parIn):
    video_url = ""
    page_data = requests.get(parIn,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':'https://livetvon.click/'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    iframe_url = preg_match(page_data, r'iframe\s*src="([^"]+)')
    logga('IFRAME DADDY: '+iframe_url)
    if iframe_url.startswith("http"):
        page_data2 = requests.get(iframe_url,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':parIn}).content
        if PY3:
            page_data2 = page_data2.decode('utf-8')
        
        iframe_url2 = preg_match(page_data2, r'iframe\s*src="([^"]+)')
        logga('IFRAME DADDY2: '+iframe_url2)
        if iframe_url2=="":
            video_url = preg_match(page_data2.replace('//source:','//source_no:'), "source:'(.*?)'")
            logga('VIDEO DADDY2: '+video_url)
            if video_url != "":
                page_m3u8 = requests.get(video_url,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':parIn}).content
                if PY3:
                    page_m3u8 = page_m3u8.decode('utf-8')
                logga('M3U8 DADDY2: '+page_m3u8)

        if "http" in iframe_url2:
            page_data3 = requests.get(iframe_url2,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':'https://widevine.licenses4.me/'}).content
            if PY3:
                page_data3 = page_data3.decode('utf-8')
            writeFileLog("DADDY_PAGE\n"+page_data3, "w+")
            video_url = preg_match(page_data3, "Clappr.Player[\w\W]*?.source:'(.*?)'")
            vt = video_url.split("?auth")
            video_url = vt[0]

    return video_url

def daddy(parIn=None):
    video_urls = []
    logga('PAR: '+parIn)
    video_url = daddyFind(parIn)
    logga('URL DADDY: '+video_url)
    arrTmp = parIn.split("stream-")
    arrTmp2 = arrTmp[1].split(".")
    vId = arrTmp2[0]
    newUrlHost="https://webudi.vhls.ru.com/lb/premium37/index.m3u8"
    rl = "https://webudi.openhd.lol/ddy1/premium"+vId+"/tracks-v1a1/mono.m3u8"
    if video_url == "":
        video_url = "https://webudi.vhls.ru.com/lb/premium"+vId+"/index.m3u8"
    
    final_url = video_url + "|connection=keepalive&Referer=https://streamservicehd.click/premiumtv/livetvon.php?id="+vId+"&User-Agent=Lavf%2F56.25.101"
    final_url3 = video_url + "|Referer=https://streamservicehd.click/&User-Agent=ipad&connection=keepalive"
    final_url2 = video_url.replace("index.m3u8", "tracks-v1a1/mono.m3u8")+"|connection=keepalive&Referer=https://streamservicehd.click/premiumtv/livetvon.php?id="+vId+"&User-Agent=Lavf%2F56.25.101"
    

    

    video_urls.append((final_url, "[COLOR lime]PLAY STREAM "+arrTmp2[0]+"[/COLOR]", "by @MandraKodi", "https://i.imgur.com/8EL6mr3.png"))
    
    """
    if "|" in video_url:
        arrV = video_url.split("|")
        video_urls.append((arrV[0], ""))		
    """
    return video_urls


def proData(parIn=None):
    video_urls = []
    logga('PAR: '+parIn)
    video_url = GetLSProData(parIn)
    logga('URL PRODATA: '+video_url)
    video_urls.append((video_url, "[COLOR lime]PLAY STREAM [/COLOR]", "by @MandraKodi"))
    return video_urls

def GetLSProData(page_in, refe=None):
    import jsunpack

    logga('page_in '+page_in)
    if refe != None:
        logga('REFER '+refe)
    if "maxstream" in page_in:
        logga('MAX STREAM')
        fu = requests.get(page_in, headers={'user-agent':'iPad','referer':page_in}).text
        find = re.findall('eval\(function(.+?.+)', fu)[0]
        unpack = jsunpack.unpack(find)
        logga('UNPACK: '+unpack)
        c = re.findall('src:"([^"]*)',unpack)[0]
        logga('URL_MARIO '+c)
        return c

    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    r = s.get(page_in, headers=headers) 

    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }

    s = requests.Session()
    page_data = s.get(page_in, headers=headers).content

    #page_data = requests.get(page_in,headers={'user-agent':'iPad','accept':'*/*','referer':refe}).content

    if PY3:
        page_data = page_data.decode('utf-8')

    src = preg_match(page_data, '<iframe src="([^"]*)')

    if src == "":
        src = preg_match(page_data, "<iframe src='([^']*)")

    if src == "": 
        src = preg_match(page_data, '<iframe width="100%" height="100%" src="([^"]*)')

    if src == "":
        src = preg_match(page_data, "<iframe allow='encrypted-media' src='([^']*)")

    if src == "":
        rsx='<iframe width="100%" height="100%" '+"allow='encrypted-media'"+' src="([^"]*)'
        logga('REGEX: '+rsx)
        src = preg_match(page_data, rsx)

    if src == "":
        try:
            c = re.findall('src="//wigistream.to/embed/([^"]*)',page_data)[0]
            src = "https://wigistream.to/embed/"+c
        except:
            pass


    src = 'https:' + src if src.startswith('//') else src
    logga('iframe_url '+src)

    if "starlive.xyz" in src:
        logga('starlive.xyz ')
        return wigi(src)
    elif "embed" in src and ("starlive" in page_in or "elixx" in page_in or "sportsembed" in page_in or "pepperlive" in page_in or "l1l1.to" in page_in):
        logga('iframe_embed for '+page_in)
    elif "buzztv" in src:
        logga('BUZZTV ')
        return GetLSProData(src)
    elif "starlive.xyz" in src:
        logga('starlive.xyz ')
        return GetLSProData(src.replace("starlive.xyz", "curvaweb"), page_in)
    elif "cloudstream" in src:
        logga('CLOUDSTREAM')
        return GetLSProData(src)
    elif "pepperlive" in src or "projectlive" in src:
        logga('PEPPER/PROJECT')
        return GetLSProData(src.replace('projectlive', 'pepperlive'))
    elif "hdmario" in src:
        logga('HDMARIO')
        return GetLSProData(src)
    else:
        logga('CALL findM3u8 FUNCTION ')
        return findM3u8(src, page_in)

    fu = requests.get(src, headers={'user-agent':'iPad','referer':page_in}).text
    try:
        find = re.findall('eval\(function(.+?.+)', fu)[0]
        unpack = jsunpack.unpack(find)
        c = re.findall('var src="([^"]*)',unpack)[0]
        return c + '|referer=' + src
    except:
        return page_in

def wigi(parIn=None):

    if parIn.startswith('http'):
        wigiUrl = parIn
    else:
        #wigiUrl = "https://starlive.xyz/embed.php?id="+parIn
        wigiUrl = "https://starlive.xyz/"+parIn

    video_urls = []
    logga('PAR_WIGI: '+parIn)
    video_url = GetLSProData(wigiUrl)
    logga('video_url '+video_url)
    msg = ""
    if video_url == '' or video_url == wigiUrl:
        video_url = parIn
        msg = "NO LINK FOUND"
    video_urls.append((video_url, msg))
    if "|" in video_url:
        arrV = video_url.split("|")
        video_urls.append((arrV[0], "LINK NO PAR"))		
    return video_urls

def urlsolver(url):
    video_urls = []

    resolvedUrl=get_resolved(url)
    if isinstance(resolvedUrl, list):
        for linkTmp in resolvedUrl:
            logga('video_tmp_url '+''.join(linkTmp))
            video_urls.append((''.join(linkTmp), "[COLOR gold]PLAY STREAM[/COLOR]"))
            return video_urls
    else:
        logga('video_resolved_url '+resolvedUrl)
        if (resolvedUrl != url):
            video_urls.append((resolvedUrl, "LINK 1"))
            if "|" in resolvedUrl:
                arrV = resolvedUrl.split("|")
                linkClean=arrV[0]
                logga('video_resolved_cleaned '+linkClean)
                video_urls.append((linkClean, "LINK 2"))		

            return video_urls
    
    return url

def resolveMyUrl(url):
    try:
        import resolveurl
    except:
        dialog = xbmcgui.Dialog()
        mess = "Lo script 'script.module.resolveurl' non risulta installato."
        dialog.ok("Mandrakodi", mess)
        return url

    xxx_plugins_path = 'special://home/addons/script.module.resolveurl.xxx/resources/plugins/'
    if xbmcvfs.exists(xxx_plugins_path):
        resolveurl.add_plugin_dirs(xbmcvfs.translatePath(xxx_plugins_path))
    resolved = ""
    try:
        resolved = resolveurl.resolve(url)
    except:
        pass
    if resolved:
        #logging.error("MANDRA URL_SOLVED: "+resolved)
        return resolved
    else:
        dialog = xbmcgui.Dialog()
        mess = "Spiacenti, ResolveUrl non ha trovato il link."
        dialog.ok("Mandrakodi", mess)
    return url


def get_resolved(url):
    resolved = daddyFind(url)
    if resolved != "" and resolved != url:
        return resolved
    else:
        logga("NO RESOLVER DADDY")		

    resolved = wizhdFind(url)
    if resolved != "" and resolved != url:
        return resolved
    else:
        logga("NO RESOLVER WIZHD")		

    resolved = assiaFind(url)
    if resolved != "" and resolved != url:
        return resolved
    else:
        logga("NO RESOLVER ASSIA")		

    resolved = GetLSProData(url)
    if resolved != "" and resolved != url:
        return resolved
    else:
        logga("NO RESOLVER DATA")		

    return resolveMyUrl(url)

def scommunity(parIn=None):
    import time, json
    base="https://streamingcommunity.online/watch/"
    
    randomUA=getRandomUA()

    headSCt={'user-agent':randomUA}
    urlComm = base + parIn
    logga("urlComm => "+urlComm)
    s = requests.Session()
    r = s.get(urlComm, headers=headSCt) 

    time.sleep(2.5)

    s = requests.Session()
    page_data = s.get(urlComm, headers=headSCt).content
    if PY3:
        page_data = page_data.decode('utf-8')
    patron = r'<video-player response="(.*?)">'
    jsonVideo = preg_match(page_data, patron)
    dataJson=jsonVideo.replace('&quot;', '"')
    arrJ = json.loads(dataJson)
    tit = (arrJ["title"]["name"]).replace("&#039;", "'").replace("&amp;", "&")
    scws_id = +arrJ["scws_id"]
    logga("scws_id => "+str(scws_id))
    return scws(str(scws_id))


def scws(parIn=None):
    import json
    video_urls = []

    base="https://streamingcommunity.online/"
    randomUA=getRandomUA()

    headSCt={'user-agent':randomUA}
    pageT = requests.get(base,headers=headSCt).content
    if PY3:
        pageT = pageT.decode('utf-8')
    patron = r'name="csrf-token" content="(.*?)"'
    csrf_token = preg_match(pageT, patron)
    logga('IP_token '+csrf_token)

    refe=base+"watch/"
    titFilm="PLAY VIDEO"
    if "___" in parIn:
        arrPar=parIn.split("___")
        parIn=arrPar[0]
        refe=base+"watch/"+arrPar[1]
    try:
        titFilm=arrPar[2]
    except:
        logga("NO TIT VIDEO")
        titFilm="PLAY VIDEO"

    
    url = "https://scws.work/master/" + str(parIn)

    def calculateToken(ip_client):
        from time import time
        from base64 import b64encode as b64
        import hashlib

        expires = int(time() + 172800)
        token = b64(hashlib.md5('{}{} Yc8U6r8KjAKAepEA'.format(expires, localIp).encode('utf-8')).digest()).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')

        s = '?token={}&expires={}&n=1'.format(token, expires)

        return s
    
    
    page_data = requests.get("http://test34344.herokuapp.com/getMyIp.php", headers={'user-agent':'Mozilla/5.0','accept':'*/*'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    logga('IP_community '+page_data)
    try:
        arrJ2 = json.loads(page_data)
        localIp = arrJ2["client_ip"]
    except:
        logga("NO LOCAL IP")

    token = calculateToken(localIp)
    
    url2 = url + token
    logga('URL_community '+url2)

    pageT = requests.get(url2,headers=headSCt).content
    if PY3:
        pageT = pageT.decode('utf-8')
    logga("MANIFEST: "+pageT)
    
    info = ""
    if pageT[0:5] != "<!DOC":
        patron=r'.*?(http[^"\s]+)'
        info = preg_match(pageT, patron, -1)

    if info:
        logga ("OK INFO")
        girancora=True
        ind=0
        cnt = len(info)
        while ind < cnt:
            url3=info[ind]
            logga('video_community '+url3)
            if "type=video" in url3:
                patron=r'rendition=(.*?)p'
                res = preg_match(url3, patron)
                url4 = url3 + "|User-Agent="+randomUA+"&Referer="+base
                video_urls.append((url4, "[COLOR gold]"+myParse.unquote(titFilm).replace("+", " ")+"[/COLOR] [COLOR blue]("+res+"p)[/COLOR]", "by @mandrakodi"))
            ind += 1
    else:
        video_url = url + token + "|User-Agent="+randomUA+"&Referer="+base
        logga('video_community '+video_url)
        video_urls.append((video_url, "[COLOR lime]"+myParse.unquote(titFilm).replace("+", " ")+"[/COLOR]", "by @mandrakodi"))
    
    remoteLog(titFilm)

    return video_urls


def pulive(parIn=None):
    url = "https://pulivetv82.com/player.html?id="+parIn
    page_data = requests.get(url, headers={'user-agent':'Mozilla/5.0','accept':'*/*'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    patron=r'window.config=(.*?)<\/script>'
    txt = preg_match(page_data, patron)
    x = txt.split("match:")
    rr=x[1]
    patron=r'source:"(.*?)"'
    txt2 = preg_match(rr, patron)
    video_urls = []
    video_urls.append((txt2+"|verifypeer=false", "[COLOR lime]PLAY STREAM[/COLOR]", "by @mandrakodi"))
    return video_urls


def macLink(parIn=None):
    from portal_api import PortalApi
    arrData = parIn.split("@PAR@")
    #0==>HOST
    #1==>MAC
    #2==>ID_CH

    host=arrData[0]
    mac=arrData[1]
    url=host+"?"+mac
    logga("PORTAL URL: "+url)
    portal = PortalApi(url)
    idCh=arrData[2]
    cmdCh="ffmpeg http://localhost/ch/"+idCh+"_"
    logga("PORTAL CMD: "+cmdCh)
    link = portal.get_link(cmdCh)
    logga("PORTAL LINK: "+link)

    try:
        link = link.split(" ")[1]
    except:
        pass

    video_urls = []
    video_urls.append((link, "[COLOR gold]PLAY CH "+idCh+"[/COLOR]"))
    return video_urls



def preg_match(data, patron, index=0):
    try:
        matches = re.findall(patron, data, flags=re.DOTALL)
        if index == -1:
            return matches

        return matches[index]
    except:
        return ""


def preg_match_all(data, patron, index=0):
    try:
        if index == 0:
            matches = re.search(patron, data, flags=re.DOTALL)
            if matches:
                if len(matches.groups()) == 1:
                    return matches.group(1)
                elif len(matches.groups()) > 1:
                    return matches.groups()
                else:
                    return matches.group()
            else:
                return ""
        else:
            matches = re.findall(patron, data, flags=re.DOTALL)
            return matches[index]
    except:
        return ""

def streamTape(parIn):
    video_urls = []
    ppIn = myParse.unquote(parIn)
    logga('PAR_STAPE: '+ppIn)
    page_data = requests.get(ppIn, headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':'https://daddylive.eu/'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    htmlCodice = preg_match(page_data, r'<\/video><script>(.*?)<\/body>')
    #iframe_url = preg_match(page_data, r'<div id="videoolink" style="display:none;">(.*?)<\/div>')
    iframe_url = preg_match(htmlCodice, r'style="display:none;">(.*?)<\/div>')
    logga('IFRAME: '+iframe_url)
    if (iframe_url != ""):
        link1 = iframe_url.split('&token=')
        linkPre = link1[0];
        logga('LINK_PRE: '+linkPre)
        #info = preg_match(page_data, r"<script>document.getElementById\('videoolink'\)(.*?)<\/script>")
        info1 = preg_match(page_data, r"<script>document.getElementById(.*?)<\/script>")
        info = info1.split(';')[0]
        tkn = preg_match(info, r"&token=(.*?)'")
        #tkn = preg_match(htmlCodice, r"&token=(.*?)'\).substring")
        linkSplit = linkPre.split("?")[1]
        info2 = "https://streamta.pe/get_video?"+linkSplit+"&token="+tkn+"&stream=1"
        logga('LINK_FINAL: '+info2)
        video_urls.append((info2, ""))
    else:
        logga('NO IFRAME')
        video_urls.append(("ignore", "[COLOR red]NO LINK FOUND[/COLOR]", ppIn))
    return video_urls

def dplay(parIn):
    import json, functools
    parIn=25081
    video_urls = []
    session = requests.Session()
    session.request = functools.partial(session.request, timeout=30)
    deviceId = uuid.uuid4().hex
    domain = 'https://' + requests.get("https://prod-realmservice.mercury.dnitv.com/realm-config/www.discoveryplus.com%2Fit%2Fepg").json()["domain"]
    apiUrl = domain + "/token?deviceId="+deviceId+"&realm=dplay&shortlived=true"
    logga('APIURL_DPLAY: '+apiUrl)
    token = session.get(apiUrl).json()['data']['attributes']['token']
    logga('TOKEN_DPLAY: '+token)
    myHeaders = {'User-Agent': 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
            'Referer': 'https://discoveryplus.it',
            'Origin': 'https://discoveryplus.it',
            'Cookie' : 'st=' + token,
            'content-type': 'application/json',
            'x-disco-params': 'realm=dplay,siteLookupKey=dplus_it'}
    session.headers = myHeaders




    content="video"
    apiUrl2 = domain + "/playback/v3/"+content+"PlaybackInfo/"
    post = {content+'Id': parIn, 'deviceInfo': {'adBlocker': False,'drmSupported': True}}
    data2 = session.post(apiUrl2, json=post).content
    data3 = json.loads(data2)
    logga('POST_DPLAY: '+str(data2))

    data = requests.get('https://eu1-prod-direct.discoveryplus.com/playback/videoPlaybackInfo/{}?usePreAuth=true'.format(parIn), headers=myHeaders).content
    logga('RESP_DPLAY: '+str(data))
    dataJ = json.loads(data)
    dataJ2=dataJ.get('data',{}).get('attributes',{})
    dataErr = "[COLOR lime]PLAY VIDEO[/COLOR]"
    try:
        if dataJ2.get('protection', {}).get('drmEnabled',False):
            link = dataJ2['streaming']['dash']['url']
            #item.drm = 'com.widevine.alpha'
            #item.license ="{}|PreAuthorization={}|R{{SSM}}|".format(data['protection']['schemes']['widevine']['licenseUrl'], data['protection']['drmToken'])
        else:
            link = dataJ2['streaming'][0]['url']
            #item.manifest = 'hls'
        #link = dataJ["data"]["attributes"]["streaming"]["hls"]["url"]
    except:
        dataErr = "[COLOR red]"+dataJ["errors"][0]["detail"]+"[/COLOR]"
        link = dataJ["errors"][0]["detail"]
    logga('LINK_DPLAY: '+link)
    video_urls.append((link, dataErr))
    return video_urls

def dplayLive(parIn):
    import json
    video_urls = []
    token = requests.get('https://disco-api.discoveryplus.it/token?realm=dplayit').json()['data']['attributes']['token']
    logga('TOKEN_DPLAY: '+token)
    headers = {'User-Agent': 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
           'Referer': 'https://discoveryplus.it',
           'Cookie' : 'st=' + token}
    data = requests.get('https://disco-api.discoveryplus.it/playback/channelPlaybackInfo/{}?usePreAuth=true'.format(parIn), headers=headers).content
    dataJ = json.loads(data)
    dataErr = "[COLOR lime]PLAY VIDEO[/COLOR]"
    try:
        link = dataJ["data"]["attributes"]["streaming"]["hls"]["url"]
    except:
        dataErr = "[COLOR red]"+dataJ["errors"][0]["detail"]+"[/COLOR]"
        link = dataJ["errors"][0]["detail"]
    logga('LINK_DPLAY: '+link)
    video_urls.append((link, dataErr))
    return video_urls

def taxi(parIn):
    import re
    video_urls = []
    url="https://eurostreaming.taxi/stream/"+parIn+".html"
    
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    r = s.get(url, headers=headers) 

    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }

    s = requests.Session()
    r = s.get(url, headers=headers)
    logga("FIND HOSTS")
    ret1 = "by @mandrakodi"
    express1 = r'<title>(.*?)</title>'
    ret1 = re.compile(express1, re.MULTILINE | re.DOTALL).findall(r.text)[0]

    #express2 = r'<a href=\"#\" allowfullscreen data-link=\"(.*?)\" id=\".*?data-num=\"(.*?)\" data-title=\"Episodio \d+\">\d+</a>'
    express2 = r'<a href="#" allowfullscreen data-link="(.*?)" id="(.*?)" data-num="(.*?)" data-title="(.*?)">\d+</a>'
    ret = re.compile(express2, re.MULTILINE | re.DOTALL).findall(r.text)
    jsonText='{"SetViewMode":"503","items":['
    numIt=0
    for (link, id, ep, tito) in ret:
        logga('LINK-TAXI: '+link+" "+ep)
        if (numIt > 0):
            jsonText = jsonText + ','    
        jsonText = jsonText + '{"title":"[COLOR lime]'+ep+'[/COLOR]","myresolve":"urlsolve@@'+link+'",'
        jsonText = jsonText + '"thumbnail":"https://www.giardiniblog.it/wp-content/uploads/2018/12/serie-tv-streaming.jpg",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"'+ret1.replace("streaming SERIE TV - euroStreaming", "")+'"}'
        numIt=numIt+1

    jsonText = jsonText + "]}"
    logga('JSON-TAXI: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls

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

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

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
        logga('OK REQUEST FROM '+url+": "+html)
    except:
        logging.warning('Error to open url: '+url)
        pass
    return html


def remoteLog(msgToLog):
    if PY3:
        import urllib.parse as myParse
    else:
        import urllib as myParse
    
    baseLog = "http://bkp34344.herokuapp.com/filter.php?numTest=JOB998"
    urlLog = baseLog + "&msgLog=" + myParse.quote(msgToLog)
    strSource = makeRequest(urlLog)
    if strSource is None or strSource == "":
        logga('MANDRA_LOG: NO REMOTE LOG')
    else:
        logga('OK REMOTE LOG')

def vudeo(parIn):
    page_in="https://vudeo.io/"+parIn+".html"
    page_data = requests.get(page_in,headers={'user-agent':'iPad','accept':'*/*','referer':page_in}).content

    if PY3:
        page_data = page_data.decode('utf-8')

    src = preg_match(page_data, 'sources: \["(.*?)"\]')
    tit = preg_match(page_data, '<title>(.*?)<\/title>')
    img = preg_match(page_data, 'poster: "(.*?)"')

    video_urls = []
    video_urls.append((src+"|referer="+page_in, "[COLOR lime]PLAY VIDEO[/COLOR]", tit.replace("Watch", ""), img))
    video_urls.append((src+"|referer="+page_in+"&verifypeer=false", "[COLOR orange]PLAY VIDEO[/COLOR]", tit.replace("Watch", ""), img))
    return video_urls

def voe(parIn):
    logga('VOE PAGE: '+parIn)
    page_data = requests.get(parIn,headers={'user-agent':'iPad','accept':'*/*','referer':parIn}).content

    if PY3:
        page_data = page_data.decode('utf-8')

    tit = preg_match(page_data, '<h1 class="mt-1">(.*?)<span')
    src = preg_match(page_data, "'hls': '(.*?)'")
    src1 = preg_match(page_data, "'mp4': '(.*?)'")

    video_urls = []
    video_urls.append((src+"|referer="+parIn, "[COLOR lime]PLAY VIDEO[/COLOR]", tit.replace(".mp4", "")))
    video_urls.append((src1+"|referer="+parIn, "[COLOR gold]PLAY VIDEO[/COLOR]", tit.replace(".mp4", "")))
    return video_urls

def getRandomUA():
    import random

    userAgentArray=[
        "Mozilla/4.0 (Mozilla/4.0; MSIE 7.0; Windows NT 5.1; FDM; SV1)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Linux i686 ; en) Opera 9.70",
        "Mozilla/4.0 (compatible; MSIE 6.0; Mac_PowerPC; en) Opera 9.24",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.24",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.26",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; es-la) Opera 9.27",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; ru) Opera 9.52",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.2; en) Opera 9.27",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.2; en) Opera 9.50",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 6.0; en) Opera 9.26",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 6.0; en) Opera 9.50",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 6.0; tr) Opera 10.10",
        "Mozilla/4.0 (compatible; MSIE 6.0; X11; Linux i686; de) Opera 10.10",
        "Mozilla/4.0 (compatible; MSIE 6.0; X11; Linux i686; en) Opera 9.22",
        "Mozilla/4.0 (compatible; MSIE 6.0; X11; Linux i686; en) Opera 9.27",
        "Mozilla/4.0 (compatible; MSIE 6.0; X11; Linux x86_64; en) Opera 9.50",
        "Mozilla/4.0 (compatible; MSIE 6.0; X11; Linux x86_64; en) Opera 9.60",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; YPC 3.2.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; YPC 3.2.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; InfoPath.2; .NET CLR 3.5.30729; .NET CLR 3.0.30618)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0;)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; .NET4.0C; .NE",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.0.3705; Media Center PC 3.1; Alexa Toolbar; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.40607)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; Alexa Toolbar; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; Alexa Toolbar)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; InfoPath.1; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; InfoPath.1)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; FDM; .NET CLR 1.1.4322)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; Media Center PC 3.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.1)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Linux i686; en) Opera 10.51",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; ko) Opera 10.53",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; pl) Opera 11.00",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; ja) Opera 11.00",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; en) Opera 10.62",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; fr) Opera 11.00",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2; O",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; Z",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8;",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8;",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8;",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; msn Optimized",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Zune 3.0)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; InfoPath.2)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; Media Center PC 6.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)",
        "Mozilla/4.0 (compatible; MSIE 8.0; X11; Linux x86_64; de) Opera 10.62",
        "Mozilla/4.0 (compatible; MSIE 8.0; X11; Linux x86_64; pl) Opera 11.00",
        "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 5.1; Trident/5.0)",
        "Mozilla/4.0 (Mozilla/4.0; MSIE 7.0; Windows NT 5.1; FDM; SV1; .NET CLR 3.0.04506.30)",
        "Mozilla/4.0 (Windows; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.59 Safari/525.19",
        "Mozilla/4.61 (Macintosh; I; PPC)",
        "Mozilla/4.61 [en] (OS/2; U)",
        "Mozilla/4.7 (compatible; OffByOne; Windows 2000)",
        "Mozilla/4.76 [en] (PalmOS; U; WebPro/3.0.1a; Palm-Arz1)",
        "Mozilla/4.79 [en] (compatible; MSIE 7.0; Windows NT 5.0; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)",
        "Mozilla/4.7C-CCK-MCD {C-UDP; EBM-APPLE} (Macintosh; I; PPC)",
        "Mozilla/4.8 [en] (Windows NT 5.0; U)",
        "Mozilla/5.0 (compatible; googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
        "Mozilla/5.0 (compatible; Yahoo! Slurp;http://help.yahoo.com/help/us/ysearch/slurp)",
        "Mozilla/5.0 (iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314",
        "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.1021.10gin_lib.cc",
        "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; es-es) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B360 Safari/531.21.10",
        "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; es-es) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
        "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
        "Mozilla/5.0 (iPhone Simulator; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7D11 Safari/531.21.10",
        "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_1 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8B117 Safari/6531.22.7",
        "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_1 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8B5097d Safari/6531.22.7",
        "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; da-dk) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
        "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; de-de) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
        "Mozilla/5.0 (iPhone; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10",
        "Mozilla/5.0 (Linux i686 ; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.70",
        "Mozilla/5.0 (Linux i686; U; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.51",
        "Mozilla/5.0 (Linux; U; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13",
        "Mozilla/5.0 (Macintosh; I; PPC Mac OS X Mach-O; en-US; rv:1.9a1) Gecko/20061204 Firefox/3.0a1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.68 Safari/534.24",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_4) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_6) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.12 Safari/534.24",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_6) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.698.0 Safari/534.24",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.68 Safari/534.24",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.0 Safari/534.24",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0b8) Gecko/20100101 Firefox/4.0b8",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X; U; en; rv:1.8.0) Gecko/20060728 Firefox/1.5.0 Opera 9.27",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_4; en-gb) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_4; en-us) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.10+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/ Safari/530.5",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-US) AppleWebKit/530.6 (KHTML, like Gecko) Chrome/ Safari/530.6",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-US) AppleWebKit/530.9 (KHTML, like Gecko) Chrome/ Safari/530.9",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.1 Safari/530.18",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/531.2+ (KHTML, like Gecko) Version/4.0.1 Safari/530.18",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-US) AppleWebKit/531.3 (KHTML, like Gecko) Chrome/3.0.192 Safari/531.3",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.196 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.198 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.212.1 Safari/532.1",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-us) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.3 Safari/531.21.10",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.197 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.198 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.207.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.208.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.210.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.2 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.8 Safari/532.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.5 Safari/532.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/532.8 (KHTML, like Gecko) Chrome/4.0.302.2 Safari/532.8",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.343.0 Safari/533.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.422.0 Safari/534.1",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.224 Safari/534.10",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.127 Safari/534.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/534.2 (KHTML, like Gecko) Chrome/6.0.453.1 Safari/534.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; es-es) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; fi-fi) AppleWebKit/531.9 (KHTML, like Gecko) Version/4.0.3 Safari/531.9",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; fr-fr) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; it-it) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; ja-jp) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; nl-nl) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; zh-cn) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; zh-tw) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.4 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.204.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.1 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.212.1 Safari/532.1",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.307.11 Safari/532.9",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.86 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_0; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.207.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.209.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.2 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.212.0 Safari/532.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.8 Safari/532.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.4 Safari/532.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.86 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; nl-nl) AppleWebKit/532.3+ (KHTML, like Gecko) Version/4.0.3 Safari/531.9",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; de-at) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/530.6 (KHTML, like Gecko) Chrome/2.0.174.0 Safari/530.6",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.343.0 Safari/533.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.366.0 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.70 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; ja-jp) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; ru-ru) AppleWebKit/533.2+ (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; ca-es) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; de-de) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; el-gr) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-au) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/531.21.11 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.363.0 Safari/533.3",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.366.0 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/533.4+ (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-US) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.428.0 Safari/534.1",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/534.1+ (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-US) AppleWebKit/534.2 (KHTML, like Gecko) Chrome/6.0.453.1 Safari/534.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.456.0 Safari/534.3",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; it-it) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; ja-jp) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; ko-kr) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; ru-ru) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; zh-cn) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.7 Safari/533.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.414.0 Safari/534.1",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.210 Safari/534.10",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.0 Safari/534.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.127 Safari/534.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.655.0 Safari/534.17",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.2 (KHTML, like Gecko) Chrome/6.0.451.0 Safari/534.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.1 Safari/534.3",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.461.0 Safari/534.3",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.464.0 Safari/534.3",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; fr-FR) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.126 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.15 Safari/534.13",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.639.0 Safari/534.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.18 (KHTML, like Gecko) Chrome/11.0.660.0 Safari/534.18",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_7_0; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.7 Safari/533.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_7_0; en-US) AppleWebKit/534.21 (KHTML, like Gecko) Chrome/11.0.678.0 Safari/534.21",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_7; en-us) AppleWebKit/533.4 (KHTML, like Gecko) Version/4.1 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-GB; rv:1.9.0.6) Gecko/2009011912 Firefox/3.0.6",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.0.10) Gecko/2009122115 Firefox/3.0.17",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.0.6) Gecko/2009011912 Firefox/3.0.6",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1b3pre) Gecko/20090204 Firefox/3.1b3pre",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 GTB5",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; fr; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; it; rv:1.9b4) Gecko/2008030317 Firefox/3.0b4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; ko; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; de; rv:1.9.0.13) Gecko/2009073021 Firefox/3.0.13",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; de; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 GTB5",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2) Gecko/20091218 Firefox 3.6b5",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.7; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en-US; rv:1.8.0.6) Gecko/20060728 Firefox/1.5.0.6",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en-US; rv:1.8.0.7) Gecko/20060909 Firefox/1.5.0.7",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en-US; rv:1.8.1) Gecko/20061024 Firefox/2.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.86 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en) AppleWebKit/418.9 (KHTML, like Gecko) Safari/419.3",
        "Mozilla/5.0 (Macintosh; U; Mac OS X 10_5_7; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/ Safari/530.5",
        "Mozilla/5.0 (Macintosh; U; Mac OS X 10_6_1; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/ Safari/530.5",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; da-dk) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; de-de) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; de) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; en) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; fr) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; hu-hu) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; ja-jp) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; nl-nl) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; tr) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_7; en-us) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; en-us) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; en-us) AppleWebKit/532.0+ (KHTML, like Gecko) Version/4.0.3 Safari/531.9",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; en-us) AppleWebKit/532.0+ (KHTML, like Gecko) Version/4.0.3 Safari/531.9.2009",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; ja-jp) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.4; en-GB; rv:1.9b5) Gecko/2008032619 Firefox/3.0b5",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.1b3pre) Gecko/20081212 Mozilla/5.0 (Windows; U; Windows NT 5.1; en) AppleWebKit/526.9 (KHTML, like Gecko) Versio",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-GB; rv:1.7.10) Gecko/20050717 Firefox/1.0.6",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:1.7.12) Gecko/20050915 Firefox/1.0.7",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:1.8.0.1) Gecko/20060214 Camino/1.0",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:1.8.0.3) Gecko/20060426 Firefox/1.5.0.3",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:1.8.0.3) Gecko/20060427 Camino/1.0.1",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:1.8.0.4) Gecko/20060613 Camino/1.0.2",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:1.8.1a2) Gecko/20060512 BonEcho/2.0a2",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:1.9a1) Gecko/20061204 Firefox/3.0a1",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-US; rv:1.8) Gecko/20051107 Camino/1.0b1",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-US) AppleWebKit/125.4 (KHTML, like Gecko, Safari) OmniWeb/v563.51",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-US) AppleWebKit/125.4 (KHTML, like Gecko, Safari) OmniWeb/v563.57",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/124 (KHTML, like Gecko) Safari/125",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/412 (KHTML, like Gecko) Safari/412",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/521.25 (KHTML, like Gecko) Safari/521.24",
        "Mozilla/5.0 (MSIE 7.0; Macintosh; U; SunOS; X11; gu; SV1; InfoPath.2; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)",
        "Mozilla/5.0 (Windows NT 5.1; rv:2.0b8pre) Gecko/20101127 Firefox/4.0b8pre",
        "Mozilla/5.0 (Windows NT 5.1; U; ; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.52",
        "Mozilla/5.0 (Windows NT 5.1; U; de; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.51",
        "Mozilla/5.0 (Windows NT 5.1; U; de; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.52",
        "Mozilla/5.0 (Windows NT 5.1; U; en-GB; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.51",
        "Mozilla/5.0 (Windows NT 5.1; U; en-GB; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.61",
        "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.0) Gecko/20060728 Firefox/1.5.0 Opera 9.22",
        "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.0) Gecko/20060728 Firefox/1.5.0 Opera 9.24",
        "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.0) Gecko/20060728 Firefox/1.5.0 Opera 9.26",
        "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.51",
        "Mozilla/5.0 (Windows NT 5.1; U; en) Opera 8.50",
        "Mozilla/5.0 (Windows NT 5.1; U; es-la; rv:1.8.0) Gecko/20060728 Firefox/1.5.0 Opera 9.27",
        "Mozilla/5.0 (Windows NT 5.1; U; Firefox/3.5; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.53",
        "Mozilla/5.0 (Windows NT 5.1; U; Firefox/4.5; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.53",
        "Mozilla/5.0 (Windows NT 5.1; U; Firefox/5.0; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.53",
        "Mozilla/5.0 (Windows NT 5.1; U; pl; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.00",
        "Mozilla/5.0 (Windows NT 5.1; U; zh-cn; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50",
        "Mozilla/5.0 (Windows NT 5.1; U; zh-cn; rv:1.8.1) Gecko/20091102 Firefox/3.5.5",
        "Mozilla/5.0 (Windows NT 5.1; U; zh-cn; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.53",
        "Mozilla/5.0 (Windows NT 5.1; U; zh-cn; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.70",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.43 Safari/534.24",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.25 (KHTML, like Gecko) Chrome/12.0.706.0 Safari/534.25",
        "Mozilla/5.0 (Windows NT 5.2; U; en; rv:1.8.0) Gecko/20060728 Firefox/1.5.0 Opera 9.27",
        "Mozilla/5.0 (Windows NT 5.2; U; ru; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.70",
        "Mozilla/5.0 (Windows NT 6.0; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.51",
        "Mozilla/5.0 (Windows NT 6.0; U; ja; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.00",
        "Mozilla/5.0 (Windows NT 6.0; U; tr; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 10.10",
        "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.34 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.699.0 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.3 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.20 Safari/535.1",
        "Mozilla/5.0 (Windows NT 6.1; rv:2.0b6pre) Gecko/20100903 Firefox/4.0b6pre Firefox/4.0b6pre",
        "Mozilla/5.0 (Windows NT 6.1; rv:2.0b7pre) Gecko/20100921 Firefox/4.0b7pre",
        "Mozilla/5.0 (Windows NT 6.1; U; en-GB; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.51",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b8pre) Gecko/20101114 Firefox/4.0b8pre",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b8pre) Gecko/20101128 Firefox/4.0b8pre",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b8pre) Gecko/20101213 Firefox/4.0b8pre",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b9pre) Gecko/20101228 Firefox/4.0b9pre",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b6pre) Gecko/20100903 Firefox/4.0b6pre",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b7) Gecko/20100101 Firefox/4.0b7",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b7) Gecko/20101111 Firefox/4.0b7",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b8pre) Gecko/20101114 Firefox/4.0b8pre",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.12 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/12.0.702.0 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.53 Safari/534.30",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.24 Safari/535.1",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.694.0 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.3 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.68 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.697.0 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.699.0 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/12.0.702.0 Safari/534.24",
        "Mozilla/5.0 (Windows NT) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20",
        "Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; el-GR)",
        "Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)",
        "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
        "Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US))",
        "Mozilla/5.0 (Windows; U; Win98; en-US; rv:1.8.0.1) Gecko/20060130 SeaMonkey/1.0",
        "Mozilla/5.0 (Windows; U; Win98; en-US; rv:1.8.1) Gecko/20061010 Firefox/2.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:0.9.2) Gecko/20020508 Netscape6/6.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:1.9.0.2) Gecko/2008092313 Firefox/3.1.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.6 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.0; ru; rv:1.9.1.13) Gecko/20100914 Firefox/3.5.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1 ; x64; en-US; rv:1.9.1b2pre) Gecko/20081026 Firefox/3.1b2pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; cs-CZ) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; cs; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de-DE) AppleWebKit/532+ (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de-DE) Chrome/4.0.223.3 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de-LI; rv:1.9.0.16) Gecko/2009120208 Firefox/3.0.16 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.2pre) Gecko/2008082305 Firefox/3.0.2pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.4) Firefox/3.0.8)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.8) Gecko/2009032609 Firefox/3.07",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.4) Gecko/20091007 Firefox/3.5.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 ( .NET CLR 3.0.04506.30)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 ( .NET CLR 3.0.04506.648)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9) Gecko/2008052906 Firefox/3.0.1pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.10) Gecko/20050716 Firefox/1.0.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.12) Gecko/20050915 Firefox/1.0.7",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.2) Gecko/20040804 Netscape/7.2 (ax)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20050519 Netscape/8.0.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20060127 Netscape/8.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.4) Gecko/20060508 Firefox/1.5.0.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.4) Gecko/20060516 SeaMonkey/1.0.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.6) Gecko/20060728 SeaMonkey/1.0.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.7) Gecko/20060909 Firefox/1.5.0.7",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1) Gecko/20060918 Firefox/2.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1) Gecko/20061003 Firefox/2.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1) Gecko/20061010 Firefox/2.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1a3) Gecko/20060527 BonEcho/2.0a3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1b1) Gecko/20060708 Firefox/2.0b1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1b2) Gecko/20060821 Firefox/2.0b2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8) Gecko/20060321 Firefox/2.0a1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8b4) Gecko/20050908 Firefox/1.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13 (.NET CLR 3.5.30729) FBSMTWB",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.16) Gecko/2009120208 Firefox/3.0.16 FBSMTWB",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.6pre) Gecko/2008121605 Firefox/3.0.6pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.6pre) Gecko/2009011606 Firefox/3.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.0 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.10) Gecko/20100504 Firefox/3.5.11 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.16) Gecko/20101130 AskTbPLTV5/3.8.0.12304 Firefox/3.5.16 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.5) Gecko/20091102 MRA 5.5 (build 02842) Firefox/3.5.5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.5) Gecko/20091102 MRA 5.5 (build 02842) Firefox/3.5.5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 (.NET CLR 3.5.30729) FBSMTWB",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 GTB6 (.NET CLR 3.5.30729) FBSMTWB",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 MRA 5.5 (build 02842) Firefox/3.5.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 MRA 5.5 (build 02842) Firefox/3.5.6 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.7) Gecko/20091221 MRA 5.5 (build 02842) Firefox/3.5.7 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b3pre) Gecko/20090213 Firefox/3.0.1b3pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b4pre) Gecko/20090401 Firefox/3.5b4pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b4pre) Gecko/20090409 Firefox/3.5b4pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b5pre) Gecko/20090517 Firefox/3.5b4pre (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.0.16 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2b4) Gecko/20091124 Firefox/3.6b4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9b1) Gecko/2007110703 Firefox/3.0b1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9b3) Gecko/2008020514 Firefox/3.0b3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9b4pre) Gecko/2008020708 Firefox/3.0b4pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9b5pre) Gecko/2008030706 Firefox/3.0b5pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.1 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.10 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.17 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.20 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.21 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.24 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.27 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.6 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.196.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.197.11 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.198.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.201.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.201.1 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.204.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.1 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.207.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.208.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.209.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.4 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.7 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.212.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML,like Gecko) Chrome/3.0.195.27",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.0 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.1 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.219.0 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.219.3 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.219.4 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.219.5 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.219.6 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.6 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.0 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.12 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.3 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.4 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.5 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.7 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.1 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.2 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.3 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.4 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.8 (KHTML, like Gecko) Chrome/4.0.288.1 Safari/532.8",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.2 Safari/533.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.353.0 Safari/533.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.355.0 Safari/533.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.356.0 Safari/533.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.357.0 Safari/533.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.8 (KHTML, like Gecko) Chrome/6.0.397.0 Safari/533.8",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.15 Safari/534.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.599.0 Safari/534.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.602.0 Safari/534.14",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.600.0 Safari/534.14",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.634.0 Safari/534.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.18 (KHTML, like Gecko) Chrome/11.0.661.0 Safari/534.18",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.19 (KHTML, like Gecko) Chrome/11.0.661.0 Safari/534.19",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.21 (KHTML, like Gecko) Chrome/11.0.678.0 Safari/534.21",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.21 (KHTML, like Gecko) Chrome/11.0.682.0 Safari/534.21",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.1 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.461.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.53 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.6 (KHTML, like Gecko) Chrome/7.0.500.0 Safari/534.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.9 (KHTML, like Gecko) Chrome/7.0.531.0 Safari/534.9",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; es-AR; rv:1.9b2) Gecko/2007121120 Firefox/3.0b2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.8.0.6) Gecko/20060728 Firefox/1.5.0.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.0.16) Gecko/2009120208 Firefox/3.0.16 FBSMTWB",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fa; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fi-FI) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr-be; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr-FR) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19 ( .NET CLR 3.5.30729; .NET4.0C)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.2b4) Gecko/20091124 Firefox/3.6b4 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.2b5) Gecko/20091204 Firefox/3.6b5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9b5) Gecko/2008032620 Firefox/3.0b5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; hu-HU) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; hu; rv:1.9.1.11) Gecko/20100701 Firefox/3.5.11",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9.0.16) Gecko/2009120208 Firefox/3.0.16 FBSMTWB",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 ( .NET CLR 3.5.30729; .NET4.0E)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9b2) Gecko/2007121120 Firefox/3.0b2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19 GTB7.0 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8 GTB7.0 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.2a1pre) Gecko/20090402 Firefox/3.6a1pre (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9b5) Gecko/2008032620 Firefox/3.0b5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ko; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ko; rv:1.9.2.4) Gecko/20100523 Firefox/3.6.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; lt; rv:1.9b4) Gecko/2008030714 Firefox/3.0b4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; nb-NO; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; nb-NO) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; nl-NL; rv:1.7.5) Gecko/20041202 Firefox/1.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; nl; rv:1.8) Gecko/20051107 Firefox/1.5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; nl; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 (.NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; nl; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; nl; rv:1.9b4) Gecko/2008030714 Firefox/3.0b4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pl; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 GTB6 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14 GTB6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.1.11) Gecko/20100701 Firefox/3.5.11 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-PT; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-PT) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU; rv:1.9.1.4) Gecko/20091016 Firefox/3.5.4 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9b3) Gecko/2008020514 Firefox/3.0b3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; sv-SE) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; tr; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 ( .NET CLR 3.5.30729; .NET4.0E)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; uk; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2.4) Gecko/20100503 Firefox/3.6.4 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9b3) Gecko/2008020514 Firefox/3.0b3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9b4) Gecko/2008030714 Firefox/3.0b4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/533.16 (KHTML, like Gecko) Chrome/5.0.335.0 Safari/533.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8 GTB6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4 GTB7.0 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW; rv:1.9b4) Gecko/2008030714 Firefox/3.0b4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; de-DE) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; de-DE) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-CA; rv:1.9.2.4) Gecko/20100523 Firefox/3.6.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.9.2.9) Gecko/20100824 Firefox/3.6.9",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.1.4) Gecko/20091007 Firefox/3.5.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.1b3pre) Gecko/20090105 Firefox/3.1b3pre",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.30 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.6 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.2.151.0 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.3.154.6 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.43 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.53 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.59 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/530.4 (KHTML, like Gecko) Chrome/2.0.172.0 Safari/530.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.43 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/531.3 (KHTML, like Gecko) Chrome/3.0.193.2 Safari/531.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.21 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.27 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.33 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.6 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.1 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.210.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.212.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.0 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.1 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.219.3 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.219.5 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.6 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.6 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.2 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.310.0 Safari/532.9",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/533.17.8 (KHTML, like Gecko) Version/5.0.1 Safari/533.17.8",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.126 Safari/533.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.540.0 Safari/534.10",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.558.0 Safari/534.10",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.652.0 Safari/534.17",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.2 (KHTML, like Gecko) Chrome/6.0.454.0 Safari/534.2",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.460.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.462.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.463.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.33 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.4 (KHTML, like Gecko) Chrome/6.0.481.0 Safari/534.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; eu) AppleWebKit/530.4 (KHTML, like Gecko) Chrome/2.0.172.0 Safari/530.4",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; fr; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 (.NET CLR 3.0.04506.648)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; fr; rv:1.9b5) Gecko/2008032620 Firefox/3.0b5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; nl; rv:1.9b5) Gecko/2008032620 Firefox/3.0b5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; zh-CN; rv:1.9.1.5) Gecko/Firefox/3.5.5",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; zh-CN; rv:1.9.2) Gecko/20091111 Firefox/3.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; zh-CN; rv:1.9.2) Gecko/20100101 Firefox/3.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; zh-TW; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0 ; x64; en-US; rv:1.9.1b2pre) Gecko/20081026 Firefox/3.1b2pre",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0 (x86_64); de-DE) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0 x64; en-US; rv:1.9.1b2pre) Gecko/20081026 Firefox/3.1b2pre",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; bg; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ca; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 GTB7.0 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; cs; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; cs; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de-AT; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de-DE) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13 (.NET CLR 4.0.20506)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 GTB5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 (.NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 GTB7.0 (.NET CLR 3.0.30618)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9b5) Gecko/2008032620 Firefox/3.0b5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; de) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19 (.NET CLR 3.5.30729) FirePHP/0.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 GTB5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 GTB5 (.NET CLR 4.0.20506)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.10) Gecko/20100504 Firefox/3.5.10 GTB7.0 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.2.9) Gecko/20100824 Firefox/3.6.9 ( .NET CLR 3.5.30729; .NET CLR 4.0.20506)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.30 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.6 Safari/525.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.2.151.0 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.2.152.0 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.2.153.0 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.4.154.31 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.42 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.43 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.46 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.50 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.53 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.59 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/528.10 (KHTML, like Gecko) Chrome/2.0.157.2 Safari/528.10",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/528.11 (KHTML, like Gecko) Chrome/2.0.157.0 Safari/528.11",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/528.8 (KHTML, like Gecko) Chrome/2.0.156.1 Safari/528.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.0 (KHTML, like Gecko) Chrome/2.0.160.0 Safari/530.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.0 (KHTML, like Gecko) Chrome/2.0.162.0 Safari/530.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.1 (KHTML, like Gecko) Chrome/2.0.164.0 Safari/530.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.1 (KHTML, like Gecko) Chrome/2.0.168.0 Safari/530.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.4 (KHTML, like Gecko) Chrome/2.0.171.0 Safari/530.4",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.2 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.23 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.39 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.40 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.43 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.6 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.173.1 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.6 (KHTML, like Gecko) Chrome/2.0.174.0 Safari/530.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.7 (KHTML, like Gecko) Chrome/2.0.176.0 Safari/530.7",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/531.3 (KHTML, like Gecko) Chrome/3.0.193.0 Safari/531.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/531.3 (KHTML, like Gecko) Chrome/3.0.193.2 Safari/531.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.1 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.10 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.17 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.20 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.21 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.27 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.3 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.6 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.196.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ja-JP) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ja-JP) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ja-JP) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ja; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ja; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 GTB6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ja; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ko; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; nb-NO) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; nl; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; nl; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; nl; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; pl-PL) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 GTB7.1 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.2) Gecko/20100115 Firefox/3.6 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9b4) Gecko/2008030714 Firefox/3.0b4",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ru-RU) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.1.5) Gecko/20091102 MRA 5.5 (build 02842) Firefox/3.5.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.2) Gecko/20100105 Firefox/3.6 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.2) Gecko/20100115 Firefox/3.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; sr; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; sv-SE; rv:1.9.0.18) Gecko/2010020220 Firefox/3.0.18 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; sv-SE; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; sv-SE; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; sv-SE; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; sv-SE; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; tr-TR) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; tr; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; x64; en-US; rv:1.9.1b2pre) Gecko/20081026 Firefox/3.1b2pre",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-CN; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-CN; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-CN; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-TW; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-TW) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ar; rv:1.9.2) Gecko/20100115 Firefox/3.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ca; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; cs; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; cs; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de-AT; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.540.0 Safari/534.10",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.224 Safari/534.10",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/10.0.649.0 Safari/534.17",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.11) Gecko/20100701 Firefox/3.5.11 ( .NET CLR 3.5.30729; .NET4.0C)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.16) Gecko/20101130 AskTbMYC/3.9.1.14019 Firefox/3.5.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1) Gecko/20090624 Firefox/3.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 4.0.20506)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.2.3) Gecko/20121221 Firefox/3.6.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.2.8) Gecko/20100722 Firefox 3.6.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3 GTB5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.3) Gecko/20100401 Firefox/3.6;MEGAUPLOAD 1.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 ( .NET CLR 3.5.30729; .NET4.0C)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.428.0 Safari/534.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729) FirePHP/0.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.1) Gecko/20090718 Firefox/3.5.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.4) Gecko/20091016 Firefox/3.5.4 (.NET CLR 3.5.30729) FBSMTWB",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.5) Gecko/20091102 MRA 5.5 (build 02842) Firefox/3.5.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1) Gecko/20090612 Firefox/3.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1) Gecko/20090612 Firefox/3.5 (.NET CLR 4.0.20506)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1) Gecko/20090624 Firefox/3.1b3;MEGAUPLOAD 1.0 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.2) Gecko/20100316 AskTbSPC2/3.9.1.14019 Firefox/3.6.2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.5.3;MEGAUPLOAD 1.0 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3pre) Gecko/20100405 Firefox/3.6.3plugin1 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.8) Gecko/20100806 Firefox/3.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2b1) Gecko/20091014 Firefox/3.6b1 GTB5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2b5) Gecko/20091204 Firefox/3.6b5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.3a3pre) Gecko/20100306 Firefox3.6 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.3.154.9 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.43 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.53 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.53 Safari/525.19",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/528.8 (KHTML, like Gecko) Chrome/1.0.156.0 Safari/528.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/528.8 (KHTML, like Gecko) Chrome/2.0.156.1 Safari/528.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/530.0 (KHTML, like Gecko) Chrome/2.0.182.0 Safari/531.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/530.4 (KHTML, like Gecko) Chrome/2.0.172.0 Safari/530.4",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.43 Safari/530.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/530.6 (KHTML, like Gecko) Chrome/2.0.174.0 Safari/530.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/531.0 (KHTML, like Gecko) Chrome/2.0.182.0 Safari/531.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/531.0 (KHTML, like Gecko) Chrome/2.0.182.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/531.0 (KHTML, like Gecko) Chrome/3.0.191.0 Safari/531.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/531.3 (KHTML, like Gecko) Chrome/3.0.193.2 Safari/531.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/531.4 (KHTML, like Gecko) Chrome/3.0.194.0 Safari/531.4",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.1 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.10 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.21 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.27 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.3 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.4 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.6 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.196.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.197.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.197.11 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.201.1 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.2 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.204.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.1 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.208.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.4 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.212.0 Safari/532.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.1 Safari/532.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.12 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.3 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.1 Safari/532.2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.3 (KHTML, like Gecko) Chrome/4.0.223.5 Safari/532.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.3 (KHTML, like Gecko) Chrome/4.0.227.0 Safari/532.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.0.246.0 Safari/532.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.0.249.0 Safari/532.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1025 Safari/532.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.307.1 Safari/532.9",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532+ (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.3 Safari/533.2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/6.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.354.0 Safari/533.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.370.0 Safari/533.4",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.999 Safari/533.4",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.9 (KHTML, like Gecko) Chrome/6.0.400.0 Safari/533.9",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.428.0 Safari/534.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.540.0 Safari/534.10",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.596.0 Safari/534.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.19 Safari/534.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.638.0 Safari/534.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.11 Safari/534.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/10.0.649.0 Safari/534.17",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.654.0 Safari/534.17",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.655.0 Safari/534.17",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.2 (KHTML, like Gecko) Chrome/6.0.454.0 Safari/534.2",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.669.0 Safari/534.20",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.1 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.459.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.460.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.461.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.464.0 Safari/534.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 GTB7.0 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; et; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.13) Gecko/20101203 AskTbBT5/3.9.1.14019 Firefox/3.6.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.13) Gecko/20101203 AskTbCDS/3.9.1.14019 Firefox/3.6.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.13) Gecko/20101203 AskTbCS2/3.9.1.14019 Firefox/3.6.13 ( .NET CLR 3.5.30729; .NET4.0C)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.13) Gecko/20101203 AskTbFXTV5/3.9.1.14019 Firefox/3.6.13 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 GTB7.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.8) Gecko/20100722 Firefox 3.6.8 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; he; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; hu; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; hu; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; hu; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.2.8) Gecko/20100722 AskTbADAP/3.9.1.14019 Firefox/3.6.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ja-JP) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ja; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ko-KR) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; lt; rv:1.9.2) Gecko/20100115 Firefox/3.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; nl; rv:1.9.0.9) Gecko/2009040821 Firefox/3.0.9 FirePHP/0.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; nl; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; pl; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; pl; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3 GTB5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; pl; rv:1.9.2.13) Gecko/20101203 AskTbUT2V5/3.9.1.14019 Firefox/3.6.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; pl; rv:1.9.2.13) Gecko/20101203 AskTbVD/3.8.0.12304 Firefox/3.6.13 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; pl; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; pt-BR; rv:1.9.2.13) Gecko/20101203 AskTbFXTV5/3.9.1.14019 Firefox/3.6.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; pt-BR; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; pt-PT; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ro; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ru-RU; rv:1.9.2) Gecko/20100105 MRA 5.6 (build 03278) Firefox/3.6 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ru-RU) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.11 Safari/534.16",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.3) Gecko/20100401 Firefox/4.0 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2b5) Gecko/20091204 Firefox/3.6b5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; sl; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; sv-SE; rv:1.9.2.13) Gecko/20101203 AskTbIMB/3.9.1.14019 Firefox/3.6.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; tr; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 GTB7.1",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; tr; rv:1.9.2.13) Gecko/20101203 AskTbCLM/3.9.1.14019 Firefox/3.6.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; uk; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 ( .NET CLR 3.5.30729; .NET4.0E)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-HK) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-TW; rv:1.9.2.13) Gecko/20101203 AskTbPTV/3.9.1.14019 Firefox/3.6.13",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-TW; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4 ( .NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-TW) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10",
        "Mozilla/5.0 (Windows; U; WinNT4.0; en-US; rv:1.8.0.5) Gecko/20060706 K-Meleon/1.0",
        "Mozilla/5.0 (Windows; Windows NT 5.1; en-US; rv:1.9.2a1pre) Gecko/20090402 Firefox/3.6a1pre",
        "Mozilla/5.0 (Windows; Windows NT 5.1; es-ES; rv:1.9.2a1pre) Gecko/20090402 Firefox/3.6a1pre",
        "Mozilla/5.0 (X11; CrOS i686 0.13.507) AppleWebKit/534.35 (KHTML, like Gecko) Chrome/13.0.763.0 Safari/534.35",
        "Mozilla/5.0 (X11; CrOS i686 0.13.587) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.14 Safari/535.1",
        "Mozilla/5.0 (X11; Linux i686; rv:2.0b3pre) Gecko/20100731 Firefox/4.0b3pre",
        "Mozilla/5.0 (X11; Linux i686; U; en; rv:1.8.0) Gecko/20060728 Firefox/1.5.0 Opera 9.23",
        "Mozilla/5.0 (X11; Linux i686; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.51",
        "Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.23 (KHTML, like Gecko) Chrome/11.0.686.3 Safari/534.23",
        "Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.14 Safari/534.24",
        "Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.702.0 Chrome/12.0.702.0 Safari/534.24",
        "Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30",
        "Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Slackware/Chrome/12.0.742.100 Safari/534.30",
        "Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.35 (KHTML, like Gecko) Ubuntu/10.10 Chromium/13.0.764.0 Chrome/13.0.764.0 Safari/534.35",
        "Mozilla/5.0 (X11; Linux x86_64; rv:2.0b4) Gecko/20100818 Firefox/4.0b4",
        "Mozilla/5.0 (X11; Linux x86_64; U; de; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.62",
        "Mozilla/5.0 (X11; Linux x86_64; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.60",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.3 Safari/534.24",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.34 Safari/534.24",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.04 Chromium/11.0.696.0 Chrome/11.0.696.0 Safari/534.24",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.703.0 Chrome/12.0.703.0 Safari/534.24",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.36 (KHTML, like Gecko) Chrome/13.0.766.0 Safari/534.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.20 Safari/535.1",
        "Mozilla/5.0 (X11; U; CrOS i686 0.9.128; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.339",
        "Mozilla/5.0 (X11; U; CrOS i686 0.9.128; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.339 Safari/534.10",
        "Mozilla/5.0 (X11; U; CrOS i686 0.9.128; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.341 Safari/534.10",
        "Mozilla/5.0 (X11; U; CrOS i686 0.9.128; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.343 Safari/534.10",
        "Mozilla/5.0 (X11; U; CrOS i686 0.9.130; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.344 Safari/534.10",
        "Mozilla/5.0 (X11; U; DragonFly i386; de; rv:1.9.1) Gecko/20090720 Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; DragonFly i386; de; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2",
        "Mozilla/5.0 (X11; U; FreeBSD i386; de-CH; rv:1.9.2.8) Gecko/20100729 Firefox/3.6.8",
        "Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.7.8) Gecko/20050609 Firefox/1.0.4",
        "Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.0.10) Gecko/20090624 Firefox/3.5",
        "Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.1) Gecko/20090703 Firefox/3.5",
        "Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.2.9) Gecko/20100913 Firefox/3.6.9",
        "Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9a2) Gecko/20080530 Firefox/3.0a2",
        "Mozilla/5.0 (X11; U; FreeBSD i386; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.207.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; FreeBSD i386; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16",
        "Mozilla/5.0 (X11; U; FreeBSD i386; ja-JP; rv:1.9.1.8) Gecko/20100305 Firefox/3.5.8",
        "Mozilla/5.0 (X11; U; FreeBSD i386; ru-RU; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3",
        "Mozilla/5.0 (X11; U; FreeBSD x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux armv7l; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux i586; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.1 Safari/533.2",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); de; rv:1.9.1) Gecko/20090624 Firefox/3.5",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); de; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.9b2) Gecko/2007121016 Firefox/3.0b2",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/530.7 (KHTML, like Gecko) Chrome/2.0.175.0 Safari/530.7",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.196.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.197.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.198.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.198.1 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.2 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.8 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/534.12 (KHTML, like Gecko) Chrome/9.0.576.0 Safari/534.12",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.634.0 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux i686 (x86_64); fr; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2",
        "Mozilla/5.0 (X11; U; Linux i686; ca; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6",
        "Mozilla/5.0 (X11; U; Linux i686; ca; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.04 (lucid) Firefox/3.6.13",
        "Mozilla/5.0 (X11; U; Linux i686; cs-CZ; rv:1.7.12) Gecko/20050929",
        "Mozilla/5.0 (X11; U; Linux i686; cs-CZ; rv:1.9.0.16) Gecko/2009121601 Ubuntu/9.04 (jaunty) Firefox/3.0.16",
        "Mozilla/5.0 (X11; U; Linux i686; cs-CZ; rv:1.9.1.6) Gecko/20100107 Fedora/3.5.6-1.fc12 Firefox/3.5.6",
        "Mozilla/5.0 (X11; U; Linux i686; cs-CZ; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.04 (lucid) Firefox/3.6.13",
        "Mozilla/5.0 (X11; U; Linux i686; de-DE; rv:1.9.2.8) Gecko/20100725 Gentoo Firefox/3.6.8",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.10) Gecko/2009042523 Ubuntu/9.04 (jaunty) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.11) Gecko/2009062218 Gentoo Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.12) Gecko/2009070811 Ubuntu/9.04 (jaunty) Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.12) Gecko/2009070812 Ubuntu/8.04 (hardy) Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.13) Gecko/2009080315 Ubuntu/9.04 (jaunty) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.14) Gecko/2009082505 Red Hat/3.0.14-1.el5_4 Firefox/3.0.14",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.14) Gecko/2009090216 Ubuntu/9.04 (jaunty) Firefox/3.0.14",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.18) Gecko/2010020400 SUSE/3.0.18-0.1.1 Firefox/3.0.18",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.18) Gecko/2010021501 Firefox/3.0.18",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.9) Gecko/2009041500 SUSE/3.0.9-2.2 Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.9) Gecko/2009042113 Ubuntu/8.04 (hardy) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.9) Gecko/2009042113 Ubuntu/8.10 (intrepid) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.9) Gecko/2009042113 Ubuntu/9.04 (jaunty) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.1) Gecko/20090714 SUSE/3.5.1-1.1 Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.1) Gecko/20090722 Gentoo Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.6) Gecko/20091201 SUSE/3.5.6-1.1.1 Firefox/3.5.6",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6 GTB7.0",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1) Gecko/20090624 Firefox/3.5",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1) Gecko/20090624 Ubuntu/8.04 (hardy) Firefox/3.5",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.10) Gecko/20100914 SUSE/3.6.10-0.3.1 Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.10) Gecko/20100915 Ubuntu/10.04 (lucid) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.10) Gecko/20100915 Ubuntu/9.10 (karmic) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.12) Gecko/20101027 Fedora/3.6.12-1.fc13 Firefox/3.6.12",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9b5) Gecko/2008041514 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9b5) Gecko/2008050509 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux i686; en-CA; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.10) Gecko/2009042513 Ubuntu/8.04 (hardy) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.10) Gecko/2009042523 Ubuntu/8.10 (intrepid) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.11) Gecko/2009060214 Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.11) Gecko/2009060308 Ubuntu/9.04 (jaunty) Firefox/3.0.11 GTB5",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.11) Gecko/2009060309 Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.13) Gecko/2009080316 Ubuntu/8.04 (hardy) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.18) Gecko/2010021501 Ubuntu/9.04 (jaunty) Firefox/3.0.18",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.19) Gecko/2010040118 Ubuntu/8.10 (intrepid) Firefox/3.0.19 GTB7.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.1.15) Gecko/20101027 Fedora/3.5.15-1.fc12 Firefox/3.5.15",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 GTB5",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6 GTB6",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.2.11) Gecko/20101013 Ubuntu/10.10 (maverick) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.10 (maverick) Firefox/3.6.12 GTB7.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9b5) Gecko/2008041514 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.13) Gecko/20060501 Epiphany/2.14",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.8) Gecko/20050511",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.9) Gecko/20050711 Firefox/1.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.2) Gecko/20060308 Firefox/1.5.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.3) Gecko/20060426 Firefox/1.5.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.4) Gecko/20060508 Firefox/1.5.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.5) Gecko/20060626 (Debian-1.8.0.5-3) Epiphany/2.14",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.6) Gecko/20060808 Fedora/1.5.0.6-2.fc5 Firefox/1.5.0.6 pango-text",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.7) Gecko/20060909 Firefox/1.5.0.7",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.7) Gecko/20060910 SeaMonkey/1.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.7) Gecko/20060928 (Debian-1.8.0.7-1) Epiphany/2.14",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.7) Gecko/20061022 Iceweasel/1.5.0.7-g2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.7) Gecko/20061031 Firefox/1.5.0.7 Flock/0.7.7",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.8) Gecko/20061029 SeaMonkey/1.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.16) Gecko/20080716 Firefox/3.07",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1) Gecko/20060601 Firefox/2.0 (Ubuntu-edgy)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1) Gecko/20061024 Iceweasel/2.0 (Debian-2.0+dfsg-1)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042513 Linux Mint/5 (Elyssa) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042523 Linux Mint/6 (Felicia) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042523 Linux Mint/7 (Gloria) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042523 Ubuntu/8.10 (intrepid) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042708 Fedora/3.0.10-1.fc10 Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042812 Gentoo Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.11) Gecko/2009060308 Linux Mint/7 (Gloria) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.11) Gecko/2009060310 Linux Mint/6 (Felicia) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.12) Gecko/2009070610 Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.12) Gecko/2009070812 Linux Mint/5 (Elyssa) Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.12) Gecko/2009070818 Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.12) Gecko/2009070818 Ubuntu/8.10 (intrepid) Firefox/3.0.12 FirePHP/0.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.13) Gecko/2009080315 Ubuntu/9.04 (jaunty) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.14) Gecko/2009090216 Ubuntu/9.04 (jaunty) Firefox/3.0.14 GTB5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.14) Gecko/2009090905 Fedora/3.0.14-1.fc10 Firefox/3.0.14",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.14) Gecko/2009091010 Firefox/3.0.14 (Debian-3.0.14-1)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.14) Gecko/20090916 Ubuntu/9.04 (jaunty) Firefox/3.0.14",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.17) Gecko/2010010604 Ubuntu/9.04 (jaunty) Firefox/3.0.17 FirePHP/0.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.19) Gecko/2010091807 Firefox/3.0.6 (Debian-3.0.6-3)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1pre) Gecko/2008062222 Firefox/3.0.1pre (Swiftfox)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008091816 Red Hat/3.0.2-3.el5 Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092000 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092313 Ubuntu/1.4.0 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.1.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-us; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.04 (jaunty) Firefox/3.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092318 Fedora/3.0.2-1.fc9 Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092418 CentOS/3.0.2-3.el5.centos Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092809 Gentoo Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008110715 ASPLinux/3.0.2-3.0.120asp Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3pre) Gecko/2008090713 Firefox/3.0.3pre (Swiftfox)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.4) Gecko/2008111318 Ubuntu/8.10 (intrepid) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.4pre) Gecko/2008101311 Firefox/3.0.4pre (Swiftfox)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.5) Gecko/2008121622 Linux Mint/6 (Felicia) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.5) Gecko/2008121718 Gentoo Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.5) Gecko/2008121914 Ubuntu/8.04 (hardy) Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.5) Gecko/2009011301 Gentoo Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009012700 SUSE/3.0.6-0.1 Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020410 Fedora/3.0.6-1.fc10 Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020410 Fedora/3.0.6-1.fc9 Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020518 Ubuntu/9.04 (jaunty) Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020616 Gentoo Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.04 (hardy) Firefox/3.0.6 FirePHP/0.2.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009022111 Gentoo Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009022714 Ubuntu/9.04 (jaunty) Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.7) Gecko/2009032018 Firefox/3.0.4 (Debian-3.0.6-1)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.9) Gecko/2009040820 Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.9) Gecko/2009041408 Red Hat/3.0.9-1.el5 Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.9) Gecko/2009042113 Linux Mint/6 (Felicia) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.9) Gecko/2009042113 Ubuntu/8.10 (intrepid) Firefox/3.0.9 GTB5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 GTB5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.2) Gecko/20090729 Slackware/13.0 Firefox/3.5.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.2pre) Gecko/20090729 Ubuntu/9.04 (jaunty) Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090912 Gentoo Firefox/3.5.3 FirePHP/0.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090919 Firefox/3.5.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.4) Gecko/20091028 Ubuntu/9.10 (karmic) Firefox/3.5.9",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.6) Gecko/20100118 Gentoo Firefox/3.5.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.9) Gecko/20100315 Ubuntu/9.10 (karmic) Firefox/3.5.9",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.9) Gecko/20100401 Ubuntu/9.10 (karmic) Firefox/3.5.9 GTB7.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1) Gecko/20090701 Ubuntu/9.04 (jaunty) Firefox/3.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1b3) Gecko/20090407 Firefox/3.1b3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.1) Gecko/20100122 firefox/3.6.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.10) Gecko/20100915 Ubuntu/9.04 (jaunty) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.2pre) Gecko/20100312 Ubuntu/9.04 (jaunty) Firefox/3.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 GTB7.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100404 Ubuntu/10.04 (lucid) Firefox/3.6.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.4) Gecko/20100625 Gentoo Firefox/3.6.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.7) Gecko/20100726 CentOS/3.6-3.el5.centos Firefox/3.6.7",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.8) Gecko/20100727 Firefox/3.6.8",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6 FirePHP/0.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2) Gecko/20100115 Ubuntu/10.04 (lucid) Firefox/3.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2) Gecko/20100128 Gentoo Firefox/3.6",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9a1) Gecko/20060814 Firefox/3.0a1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b2) Gecko/2007121016 Firefox/3.0b2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b3) Gecko/2008020513 Firefox/3.0b3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b3pre) Gecko/2008010415 Firefox/3.0b",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b3pre) Gecko/2008020507 Firefox/3.0b3pre",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b4) Gecko/2008031317 Firefox/3.0b4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b4pre) Gecko/2008021712 Firefox/3.0b4pre (Swiftfox)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b4pre) Gecko/2008021714 Firefox/3.0b4pre (Swiftfox)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b5) Gecko/2008050509 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9pre) Gecko/2008040318 Firefox/3.0pre (Swiftfox)",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/531.4 (KHTML, like Gecko) Chrome/3.0.194.0 Safari/531.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.1 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.196.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.197.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.197.11 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.198.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.198.1 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.202.2 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.2 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.204.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.205.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.1 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.207.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.209.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.2 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.212.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.212.0 Safari/532.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.0 Safari/532.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.1 Safari/532.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.0 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.8 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.2 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.3 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.4 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.5 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.6 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.8 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.1 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.2 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.4 (KHTML, like Gecko) Chrome/4.0.237.0 Safari/532.4 Debian",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.8 (KHTML, like Gecko) Chrome/4.0.277.0 Safari/532.8",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.358.0 Safari/533.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.366.2 Safari/533.4",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.416.0 Safari/534.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.1 SUSE/6.0.428.0 (KHTML, like Gecko) Chrome/6.0.428.0 Safari/534.1",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.551.0 Safari/534.10",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.12 (KHTML, like Gecko) Chrome/9.0.579.0 Safari/534.12",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.44 Safari/534.13",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.84 Safari/534.13",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Ubuntu/9.10 Chromium/9.0.592.0 Chrome/9.0.592.0 Safari/534.13",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Chrome/10.0.612.1 Safari/534.15",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Ubuntu/10.04 Chromium/10.0.612.3 Chrome/10.0.612.3 Safari/534.15",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.611.0 Chrome/10.0.611.0 Safari/534.15",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.613.0 Chrome/10.0.613.0 Safari/534.15",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.0 Chrome/10.0.648.0 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.133 Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.2 (KHTML, like Gecko) Chrome/6.0.453.1 Safari/534.2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.457.0 Safari/534.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.0 Safari/534.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.460.0 Safari/534.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.462.0 Safari/534.3",
        "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.24 Safari/534.7",
        "Mozilla/5.0 (X11; U; Linux i686; en; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.10 (intrepid) Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.0.4) Gecko/2008111317 Linux Mint/5 (Elyssa) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.0.4) Gecko/2008111317 Ubuntu/8.04 (hardy) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.0.9) Gecko/2009042113 Ubuntu/9.04 (jaunty) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9b5) Gecko/2008041514 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.10) Gecko/2009042513 Linux Mint/5 (Elyssa) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.10) Gecko/2009042523 Ubuntu/9.04 (jaunty) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.11) Gecko/2009060309 Linux Mint/5 (Elyssa) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.11) Gecko/2009060310 Ubuntu/8.10 (intrepid) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.11) Gecko/2009061118 Fedora/3.0.11-1.fc9 Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.14) Gecko/2009090216 Firefox/3.0.14",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.1.6) Gecko/20091201 SUSE/3.5.6-1.1.1 Firefox/3.5.6 GTB6",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.1.7) Gecko/20091222 SUSE/3.5.7-1.1.1 Firefox/3.5.7",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.1.9) Gecko/20100317 SUSE/3.5.9-0.1 Firefox/3.5.9",
        "Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.2.13) Gecko/20101206 Ubuntu/9.10 (karmic) Firefox/3.6.13",
        "Mozilla/5.0 (X11; U; Linux i686; eu; rv:1.9.0.6) Gecko/2009012700 SUSE/3.0.6-0.1.2 Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; fi-FI; rv:1.9.0.11) Gecko/2009060308 Ubuntu/9.04 (jaunty) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; fi-FI; rv:1.9.0.13) Gecko/2009080315 Linux Mint/6 (Felicia) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux i686; fi-FI; rv:1.9.0.5) Gecko/2008121622 Ubuntu/8.10 (intrepid) Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; fi-FI; rv:1.9.0.9) Gecko/2009042113 Ubuntu/9.04 (jaunty) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; fi-FI; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8",
        "Mozilla/5.0 (X11; U; Linux i686; fr-be; rv:1.9.0.8) Gecko/2009073022 Ubuntu/9.04 (jaunty) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux i686; fr-FR; rv:1.9.0.5) Gecko/2008123017 Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; fr-FR; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5",
        "Mozilla/5.0 (X11; U; Linux i686; fr-FR; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.10) Gecko/2009042513 Ubuntu/8.04 (hardy) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.10) Gecko/2009042708 Fedora/3.0.10-1.fc10 Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.2) Gecko/2008092318 Fedora/3.0.2-1.fc9 Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.03",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.7) Gecko/2009030422 Ubuntu/8.10 (intrepid) Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.7) Gecko/2009031218 Gentoo Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.9) Gecko/2009042113 Ubuntu/8.04 (hardy) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.0.9) Gecko/2009042113 Ubuntu/9.04 (jaunty) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.1) Gecko/20090624 Firefox/3.5",
        "Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2",
        "Mozilla/5.0 (X11; U; Linux i686; hu-HU; rv:1.9.0.10) Gecko/2009042718 CentOS/3.0.10-1.el5.centos Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; hu-HU; rv:1.9.0.7) Gecko/2009030422 Ubuntu/8.10 (intrepid) Firefox/3.0.7 FirePHP/0.2.4",
        "Mozilla/5.0 (X11; U; Linux i686; hu-HU; rv:1.9.1.9) Gecko/20100330 Fedora/3.5.9-1.fc12 Firefox/3.5.9",
        "Mozilla/5.0 (X11; U; Linux i686; it-IT; rv:1.9.0.11) Gecko/2009060308 Linux Mint/7 (Gloria) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; it-IT; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.04 (jaunty) Firefox/3.5",
        "Mozilla/5.0 (X11; U; Linux i686; it-IT; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.25 (jaunty) Firefox/3.8",
        "Mozilla/5.0 (X11; U; Linux i686; it; rv:1.9.0.11) Gecko/2009061118 Fedora/3.0.11-1.fc10 Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; it; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; it; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; it; rv:1.9.0.4) Gecko/2008111217 Red Hat Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; it; rv:1.9.0.5) Gecko/2008121711 Ubuntu/9.04 (jaunty) Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; it; rv:1.9) Gecko/2008061015 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux i686; ja-JP; rv:1.9.1.8) Gecko/20100216 Fedora/3.5.8-1.fc12 Firefox/3.5.8",
        "Mozilla/5.0 (X11; U; Linux i686; ja; rv:1.9.0.5) Gecko/2008121622 Ubuntu/8.10 (intrepid) Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; ja; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (X11; U; Linux i686; ko-KR; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; ko-KR; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.10 (maverick) Firefox/3.6.12",
        "Mozilla/5.0 (X11; U; Linux i686; ko-KR; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3",
        "Mozilla/5.0 (X11; U; Linux i686; nl-NL; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4",
        "Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9.0.11) Gecko/2009060308 Ubuntu/9.04 (jaunty) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9.0.11) Gecko/2009060309 Ubuntu/8.04 (hardy) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9.0.4) Gecko/2008111317 Ubuntu/8.04 (hardy) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9.1.9) Gecko/20100401 Ubuntu/9.10 (karmic) Firefox/3.5.9",
        "Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9) Gecko/2008061015 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.1) Gecko/2008071222 Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.1) Gecko/2008071719 Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.10) Gecko/2009042513 Ubuntu/8.04 (hardy) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.13) Gecko/2009080315 Ubuntu/9.04 (jaunty) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.25 (jaunty) Firefox/3.8",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.2) Gecko/20121223 Ubuntu/9.25 (jaunty) Firefox/3.8",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.3) Gecko/2008092700 SUSE/3.0.3-2.2 Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.4) Gecko/20081031100 SUSE/3.0.4-4.6 Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.5) Gecko/2008121300 SUSE/3.0.5-0.1 Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.5) Gecko/2008121622 Slackware/2.6.27-PiP Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.10 (intrepid) Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.7) Gecko/2009030422 Kubuntu/8.10 (intrepid) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.7) Gecko/2009030503 Fedora/3.0.7-1.fc10 Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.9) Gecko/2009042113 Ubuntu/8.10 (intrepid) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.2.10) Gecko/20100915 Ubuntu/10.04 (lucid) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9b4) Gecko/2008030800 SUSE/2.9.94-4.2 Firefox/3.0b4",
        "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9b5) Gecko/2008050509 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux i686; pl; rv:1.9.0.6) Gecko/2009011912 Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; pt-BR; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux i686; pt-BR; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; pt-BR; rv:1.9.0.4) Gecko/2008111217 Fedora/3.0.4-1.fc10 Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; pt-BR; rv:1.9.0.4) Gecko/2008111317 Ubuntu/8.04 (hardy) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; pt-PT; rv:1.9.0.5) Gecko/2008121622 Ubuntu/8.10 (intrepid) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux i686; ru-RU; rv:1.9.1.2) Gecko/20090804 Firefox/3.5.2",
        "Mozilla/5.0 (X11; U; Linux i686; ru-RU; rv:1.9.2a1pre) Gecko/20090405 Ubuntu/9.04 (jaunty) Firefox/3.6a1pre",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.0.1) Gecko/2008071719 Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.0.5) Gecko/2008120121 Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.0.5) Gecko/2008121622 Ubuntu/8.10 (intrepid) Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.1.3) Gecko/20091020 Ubuntu/9.10 (karmic) Firefox/3.5.3",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.3a5pre) Gecko/20100526 Firefox/3.7a5pre",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9) Gecko/2008061812 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9b5) Gecko/2008032600 SUSE/2.9.95-25.1 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux i686; rv:1.9) Gecko/2008080808 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux i686; rv:1.9) Gecko/20080810020329 Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux i686; sk; rv:1.9.0.5) Gecko/2008121621 Ubuntu/8.04 (hardy) Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; sk; rv:1.9.1) Gecko/20090630 Fedora/3.5-1.fc11 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux i686; sk; rv:1.9) Gecko/2008061015 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux i686; sv-SE; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; sv-SE; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux i686; tr-TR; rv:1.9.0.10) Gecko/2009042523 Ubuntu/9.04 (jaunty) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux i686; tr-TR; rv:1.9.0) Gecko/2008061600 SUSE/3.0-1.2 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux i686; tr-TR; rv:1.9b5) Gecko/2008032600 SUSE/2.9.95-25.1 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux i686; zh-CN; rv:1.9.1.6) Gecko/20091216 Fedora/3.5.6-1.fc11 Firefox/3.5.6 GTB6",
        "Mozilla/5.0 (X11; U; Linux i686; zh-CN; rv:1.9.1.8) Gecko/20100216 Fedora/3.5.8-1.fc12 Firefox/3.5.8",
        "Mozilla/5.0 (X11; U; Linux i686; zh-CN; rv:1.9.2.8) Gecko/20100722 Ubuntu/10.04 (lucid) Firefox/3.6.8",
        "Mozilla/5.0 (X11; U; Linux i686; zh-TW; rv:1.9.0.13) Gecko/2009080315 Ubuntu/9.04 (jaunty) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux i686; zh-TW; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux i686; zh-TW; rv:1.9.0.7) Gecko/2009030422 Ubuntu/8.04 (hardy) Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux ia64; en-US; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux ppc; en-GB; rv:1.9.0.12) Gecko/2009070818 Ubuntu/8.10 (intrepid) Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux ppc; en-US; rv:1.9.0.4) Gecko/2008111317 Ubuntu/8.04 (hardy) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux x64_64; es-AR; rv:1.9.0.3) Gecko/2008092515 Ubuntu/8.10 (intrepid) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:1.9.0.4) Gecko/2008111318 Ubuntu/8.04 (hardy) Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:1.9.1.7) Gecko/20100106 Ubuntu/9.10 (karmic) Firefox/3.5.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:1.9.1.9) Gecko/20100317 SUSE/3.5.9-0.1.1 Firefox/3.5.9",
        "Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:1.9.2.10) Gecko/20100915 Ubuntu/10.04 (lucid) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; da-DK; rv:1.9.0.10) Gecko/2009042523 Ubuntu/9.04 (jaunty) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.0.1) Gecko/2008070400 SUSE/3.0.1-0.1 Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.0.11) Gecko/2009070611 Gentoo Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.0.18) Gecko/2010021501 Ubuntu/9.04 (jaunty) Firefox/3.0.18",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.0.3) Gecko/2008090713 Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.0.7) Gecko/2009030620 Gentoo Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.0.9) Gecko/2009042114 Ubuntu/9.04 (jaunty) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.1.10) Gecko/20100506 SUSE/3.5.10-0.1.1 Firefox/3.5.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10 GTB7.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2.3) Gecko/20100401 SUSE/3.6.3-1.1 Firefox/3.6.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2) Gecko/20100308 Ubuntu/10.04 (lucid) Firefox/3.6",
        "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9) Gecko/2008061017 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; el-GR; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-ca) AppleWebKit/531.2+ (KHTML, like Gecko) Version/5.0 Safari/531.2+",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.8.0.4) Gecko/20060608 Ubuntu/dapper-security Epiphany/2.14",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.1) Gecko/2008072820 Firefox/3.0.1 FirePHP/0.1.1.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.10) Gecko/2009042523 Ubuntu/9.04 (jaunty) Firefox/3.0.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.11) Gecko/2009060308 Ubuntu/9.04 (jaunty) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.12) Gecko/2009070811 Ubuntu/9.04 (jaunty) Firefox/3.0.12 FirePHP/0.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.2) Gecko/2008092213 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.5) Gecko/2008122010 Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.7) Gecko/2009030503 Fedora/3.0.7-1.fc9 Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.8) Gecko/2009032712 Ubuntu/8.10 (intrepid) Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.8) Gecko/2009032712 Ubuntu/8.10 (intrepid) Firefox/3.0.8 FirePHP/0.2.4",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.0.9) Gecko/2009042113 Ubuntu/8.10 (intrepid) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.7.6) Gecko/20050512 Firefox",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.1) Gecko/2008072820 Kubuntu/8.04 (hardy) Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.1) Gecko/2008110312 Gentoo Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.11) Gecko/2009060309 Linux Mint/7 (Gloria) Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.11) Gecko/2009061118 Fedora/3.0.11-1.fc9 Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.11) Gecko/2009061417 Gentoo Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.11) Gecko/2009070612 Gentoo Firefox/3.0.11",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.12) Gecko/2009070811 Ubuntu/9.04 (jaunty) Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.12) Gecko/2009070818 Ubuntu/8.10 (intrepid) Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.13) Gecko/2009080315 Ubuntu/9.04 (jaunty) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.14) Gecko/2009090217 Ubuntu/9.04 (jaunty) Firefox/3.0.13",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.14) Gecko/2009090217 Ubuntu/9.04 (jaunty) Firefox/3.0.14",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.16) Gecko/2009121609 Firefox/3.0.6 (Windows NT 5.1)",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.17) Gecko/2010011010 Mandriva/1.9.0.17-0.1mdv2009.1 (2009.1) Firefox/3.0.17 GTB6",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.2) Gecko/2008092213 Ubuntu/8.04 (hardy) Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.2) Gecko/2008092318 Fedora/3.0.2-1.fc9 Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.2) Gecko/2008092418 CentOS/3.0.2-3.el5.centos Firefox/3.0.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3 (Linux Mint)",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.4) Gecko/2008120512 Gentoo Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.5) Gecko/2008121711 Ubuntu/9.04 (jaunty) Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.5) Gecko/2008121806 Gentoo Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.5) Gecko/2008121911 CentOS/3.0.5-1.el5.centos Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.5) Gecko/2008122014 CentOS/3.0.5-1.el4.centos Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.5) Gecko/2008122120 Gentoo Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.5) Gecko/2008122406 Gentoo Firefox/3.0.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.6) Gecko/2009012700 SUSE/3.0.6-1.4 Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.6) Gecko/2009020407 Firefox/3.0.4 (Debian-3.0.6-1)",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.6) Gecko/2009020519 Ubuntu/9.04 (jaunty) Firefox/3.0.6",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009030423 Ubuntu/8.10 (intrepid) Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009030516 Ubuntu/9.04 (jaunty) Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009030516 Ubuntu/9.04 (jaunty) Firefox/3.0.7 GTB5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009030719 Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009030810 Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009031120 Mandriva Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009031120 Mandriva/1.9.0.7-0.1mdv2009.0 (2009.0) Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009031802 Gentoo Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009032319 Gentoo Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.7) Gecko/2009032606 Red Hat/3.0.7-1.el5 Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009032600 SUSE/3.0.8-1.1 Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009032600 SUSE/3.0.8-1.1.1 Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009032712 Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009032712 Ubuntu/8.04 (hardy) Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009032712 Ubuntu/8.10 (intrepid) Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009032713 Ubuntu/9.04 (jaunty) Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009032908 Gentoo Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009033100 Ubuntu/9.04 (jaunty) Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009040312 Gentoo Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0) Gecko/2008061600 SUSE/3.0-1.2 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.1) Gecko/20090714 SUSE/3.5.1-1.1 Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.1) Gecko/20090716 Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.1) Gecko/20090716 Linux Mint/7 (Gloria) Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.15) Gecko/20101027 Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.540.",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.2) Gecko/20090803 Firefox/3.5.2 Slackware",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.2) Gecko/20090803 Slackware Firefox/3.5.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3) Gecko/20090914 Slackware/13.0_stable Firefox/3.5.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.5) Gecko/20091114 Gentoo Firefox/3.5.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.6) Gecko/20100117 Gentoo Firefox/3.5.6",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.8) Gecko/20100318 Gentoo Firefox/3.5.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.8pre) Gecko/20091227 Ubuntu/9.10 (karmic) Firefox/3.5.5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1) Gecko/20090630 Firefox/3.5 GTB6",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1b3) Gecko/20090312 Firefox/3.1b3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1b3) Gecko/20090327 Fedora/3.1-0.11.beta3.fc11 Firefox/3.1b3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1b3) Gecko/20090327 GNU/Linux/x86_64 Firefox/3.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10 GTB7.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101102 Firefox/3.6.12",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101102 Gentoo Firefox/3.6.12",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101206 Firefox/3.6.13",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101219 Gentoo Firefox/3.6.13",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101223 Gentoo Firefox/3.6.13",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.3) Gecko/20100403 Firefox/3.6.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.3) Gecko/20100524 Firefox/3.5.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.4) Gecko/20100614 Ubuntu/10.04 (lucid) Firefox/3.6.4",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6 GTB7.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6 GTB7.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.7) Gecko/20100723 Fedora/3.6.7-1.fc13 Firefox/3.6.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.7) Gecko/20100809 Fedora/3.6.7-1.fc14 Firefox/3.6.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.8) Gecko/20100723 SUSE/3.6.8-0.1.1 Firefox/3.6.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.8) Gecko/20100804 Gentoo Firefox/3.6.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.9) Gecko/20100915 Gentoo Firefox/3.6.9",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100130 Gentoo Firefox/3.6",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100222 Ubuntu/10.04 (lucid) Firefox/3.6",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100305 Gentoo Firefox/3.5.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2a1pre) Gecko/20090405 Firefox/3.6a1pre",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2a1pre) Gecko/20090428 Firefox/3.6a1pre",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9) Gecko/2008061317 (Gentoo) Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9) Gecko/2008062315 (Gentoo) Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9) Gecko/2008062908 Firefox/3.0 (Debian-3.0~rc2-2)",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9b3pre) Gecko/2008011321 Firefox/3.0b3pre",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9b3pre) Gecko/2008020509 Firefox/3.0b3pre",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9b4) Gecko/2008031318 Firefox/3.0b4",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9b4) Gecko/2008040813 Firefox/3.0b4",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9b5) Gecko/2008040514 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9b5) Gecko/2008041816 Fedora/3.0-0.55.beta5.fc9 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9pre) Gecko/2008042312 Firefox/3.0b5",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.203.2 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.204.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.206.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.207.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.208.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.209.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.2 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.212.0 Safari/532.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.0 Safari/532.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.1 Safari/532.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.219.3 Safari/532.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.3 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.221.7 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.1 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.4 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.5 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.222.6 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Chrome/4.0.223.2 Safari/532.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.308.0 Safari/532.9",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.309.0 Safari/532.9",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/533.1 (KHTML, like Gecko) Chrome/5.0.335.0 Safari/533.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.1 Safari/533.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.3 Safari/533.2",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.353.0 Safari/533.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.354.0 Safari/533.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.358.0 Safari/533.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.368.0 Safari/533.4",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.417.0 Safari/534.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.427.0 Safari/534.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.544.0 Safari/534.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.200 Safari/534.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Ubuntu/10.10 Chromium/8.0.552.237 Chrome/8.0.552.237 Safari/534.10",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Ubuntu/10.04 Chromium/9.0.595.0 Chrome/9.0.595.0 Safari/534.13",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Ubuntu/10.10 Chromium/9.0.600.0 Chrome/9.0.600.0 Safari/534.14",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Chrome/10.0.613.0 Safari/534.15",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.11 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.127 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.82 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.642.0 Chrome/10.0.642.0 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.0 Chrome/10.0.648.0 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.127 Chrome/10.0.648.127 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.133 Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 SUSE/10.0.626.0 (KHTML, like Gecko) Chrome/10.0.626.0 Safari/534.16",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.1 Safari/534.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.470.0 Safari/534.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/540.0 (KHTML, like Gecko) Ubuntu/10.10 Chrome/8.1.0.0 Safari/540.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/540.0 (KHTML, like Gecko) Ubuntu/10.10 Chrome/9.1.0.0 Safari/540.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/540.0 (KHTML,like Gecko) Chrome/9.1.0.0 Safari/540.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US) Gecko Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-AR; rv:1.9.0.3) Gecko/2008092515 Ubuntu/8.10 (intrepid) Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-AR; rv:1.9.0.4) Gecko/2008110510 Red Hat/3.0.4-1.el5_2 Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-AR; rv:1.9) Gecko/2008061015 Ubuntu/8.04 (hardy) Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-AR; rv:1.9) Gecko/2008061017 Firefox/3.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-CL; rv:1.9.1.9) Gecko/20100402 Ubuntu/9.10 (karmic) Firefox/3.5.9",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.0.1) Gecko/2008072820 Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.0.12) Gecko/2009070811 Ubuntu/9.04 (jaunty) Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.0.12) Gecko/2009072711 CentOS/3.0.12-1.el5.centos Firefox/3.0.12",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.0.4) Gecko/2008111217 Fedora/3.0.4-1.fc10 Firefox/3.0.4",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.0.7) Gecko/2009022800 SUSE/3.0.7-1.4 Firefox/3.0.7",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.0.9) Gecko/2009042114 Ubuntu/9.04 (jaunty) Firefox/3.0.9",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.1.8) Gecko/20100216 Fedora/3.5.8-1.fc11 Firefox/3.5.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.2.12) Gecko/20101027 Fedora/3.6.12-1.fc13 Firefox/3.6.12",
        "Mozilla/5.0 (X11; U; Linux x86_64; es-MX; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.04 (lucid) Firefox/3.6.12",
        "Mozilla/5.0 (X11; U; Linux x86_64; fi-FI; rv:1.9.0.14) Gecko/2009090217 Firefox/3.0.14",
        "Mozilla/5.0 (X11; U; Linux x86_64; fi-FI; rv:1.9.0.8) Gecko/2009032712 Ubuntu/8.10 (intrepid) Firefox/3.0.8",
        "Mozilla/5.0 (X11; U; Linux x86_64; fr-FR) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7",
        "Mozilla/5.0 (X11; U; Linux x86_64) Gecko/2008072820 Firefox/3.0.1",
        "Mozilla/5.0 (X11; U; Linux x86; es-ES; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3",
        "Mozilla/5.0 (X11; U; Linux x86; rv:1.9.1.1) Gecko/20090716 Linux Firefox/3.5.1",
        "Mozilla/5.0 ArchLinux (X11; U; Linux x86_64; en-US) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100",
        "Mozilla/5.0 ArchLinux (X11; U; Linux x86_64; en-US) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30",
        "Mozilla/5.0 ArchLinux (X11; U; Linux x86_64; en-US) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.60 Safari/534.30",
        "Mozilla/5.0 Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.13) Firefox/3.6.13",
        "Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10",
        "Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10gin_lib.cc",
        "Mozilla/5.0(Windows; U; Windows NT 5.2; rv:1.9.2) Gecko/20100101 Firefox/3.6",
        "Mozilla/6.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:2.0.0.0) Gecko/20061028 Firefox/3.0",
        "Mozilla/6.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.8",
        "Mozilla/6.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.8 (.NET CLR 3.5.30729)",
        "Mozilla/6.0 (Windows; U; Windows NT 6.0; en-US) Gecko/2009032609 (KHTML, like Gecko) Chrome/2.0.172.6 Safari/530.7",
        "Mozilla/6.0 (Windows; U; Windows NT 6.0; en-US) Gecko/2009032609 Chrome/2.0.172.6 Safari/530.7",
        "Mozilla/6.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.27 Safari/532.0",
        "Mozilla/6.0 (Windows; U; Windows NT 7.0; en-US; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.9 (.NET CLR 3.5.30729)",
        "Opera 9.4 (Windows NT 5.3; U; en)",
        "Opera 9.4 (Windows NT 6.1; U; en)",
        "Opera 9.7 (Windows NT 5.2; U; en)",
        "Opera/10.50 (Windows NT 6.1; U; en-GB) Presto/2.2.2",
        "Opera/10.60 (Windows NT 5.1; U; en-US) Presto/2.6.30 Version/10.60",
        "Opera/10.60 (Windows NT 5.1; U; zh-cn) Presto/2.6.30 Version/10.60",
        "Opera/2.0.3920 (J2ME/MIDP; Opera Mini; en; U; ssr)",
        "Opera/7.23 (Windows 98; U) [en]",
        "Opera/8.0 (X11; Linux i686; U; cs)",
        "Opera/8.00 (Windows NT 5.1; U; en)",
        "Opera/8.01 (J2ME/MIDP; Opera Mini/2.0.4062; en; U; ssr)",
        "Opera/8.01 (J2ME/MIDP; Opera Mini/2.0.4509/1316; fi; U; ssr)",
        "Opera/8.01 (J2ME/MIDP; Opera Mini/2.0.4719; en; U; ssr)",
        "Opera/8.02 (Qt embedded; Linux armv4ll; U) [en] SONY/COM1",
        "Opera/8.02 (Windows NT 5.1; U; en)",
        "Opera/8.5 (X11; Linux i686; U; cs)",
        "Opera/8.50 (Windows NT 5.1; U; en)",
        "Opera/8.51 (Windows NT 5.1; U; en)",
        "Opera/9.0 (Windows NT 5.0; U; en)",
        "Opera/9.00 (Macintosh; PPC Mac OS X; U; en)",
        "Opera/9.00 (Wii; U; ; 1038-58; Wii Shop Channel/1.0; en)",
        "Opera/9.00 (Windows NT 5.1; U; en)",
        "Opera/9.00 (Windows NT 5.2; U; en)",
        "Opera/9.00 (Windows NT 6.0; U; en)",
        "Opera/9.01 (X11; Linux i686; U; en)",
        "Opera/9.02 (Windows NT 5.1; U; en)",
        "Opera/9.10 (Windows NT 5.1; U; es-es)",
        "Opera/9.10 (Windows NT 5.1; U; fi)",
        "Opera/9.10 (Windows NT 5.1; U; hu)",
        "Opera/9.10 (Windows NT 5.1; U; it)",
        "Opera/9.10 (Windows NT 5.1; U; MEGAUPLOAD 1.0; pl)",
        "Opera/9.10 (Windows NT 5.1; U; nl)",
        "Opera/9.10 (Windows NT 5.1; U; pl)",
        "Opera/9.10 (Windows NT 5.1; U; pt)",
        "Opera/9.10 (Windows NT 5.1; U; sv)",
        "Opera/9.10 (Windows NT 5.1; U; zh-tw)",
        "Opera/9.10 (Windows NT 5.2; U; de)",
        "Opera/9.10 (Windows NT 5.2; U; en)",
        "Opera/9.10 (Windows NT 6.0; U; en)",
        "Opera/9.10 (Windows NT 6.0; U; it-IT)",
        "Opera/9.10 (X11; Linux i386; U; en)",
        "Opera/9.10 (X11; Linux i686; U; en)",
        "Opera/9.10 (X11; Linux i686; U; kubuntu;pl)",
        "Opera/9.10 (X11; Linux i686; U; pl)",
        "Opera/9.10 (X11; Linux x86_64; U; en)",
        "Opera/9.10 (X11; Linux; U; en)",
        "Opera/9.12 (Windows NT 5.0; U; ru)",
        "Opera/9.12 (Windows NT 5.0; U)",
        "Opera/9.12 (X11; Linux i686; U; en) (Ubuntu)",
        "Opera/9.20 (Windows NT 5.1; U; en)",
        "Opera/9.20 (Windows NT 5.1; U; es-AR)",
        "Opera/9.20 (Windows NT 5.1; U; es-es)",
        "Opera/9.20 (Windows NT 5.1; U; it)",
        "Opera/9.20 (Windows NT 5.1; U; MEGAUPLOAD=1.0; es-es)",
        "Opera/9.20 (Windows NT 5.1; U; nb)",
        "Opera/9.20 (Windows NT 5.1; U; zh-tw)",
        "Opera/9.20 (Windows NT 5.2; U; en)",
        "Opera/9.20 (Windows NT 6.0; U; de)",
        "Opera/9.20 (Windows NT 6.0; U; en)",
        "Opera/9.20 (Windows NT 6.0; U; es-es)",
        "Opera/9.20 (X11; Linux i586; U; en)",
        "Opera/9.20 (X11; Linux i686; U; en)",
        "Opera/9.20 (X11; Linux i686; U; es-es)",
        "Opera/9.20 (X11; Linux i686; U; pl)",
        "Opera/9.20 (X11; Linux i686; U; ru)",
        "Opera/9.20 (X11; Linux i686; U; tr)",
        "Opera/9.20 (X11; Linux ppc; U; en)",
        "Opera/9.20 (X11; Linux x86_64; U; en)",
        "Opera/9.20(Windows NT 5.1; U; en)",
        "Opera/9.21 (Macintosh; Intel Mac OS X; U; en)",
        "Opera/9.21 (Macintosh; PPC Mac OS X; U; en)",
        "Opera/9.21 (Windows 98; U; en)",
        "Opera/9.21 (Windows NT 5.0; U; de)",
        "Opera/9.21 (Windows NT 5.1; U; de)",
        "Opera/9.21 (Windows NT 5.1; U; en)",
        "Opera/9.21 (Windows NT 5.1; U; fr)",
        "Opera/9.21 (Windows NT 5.1; U; MEGAUPLOAD 1.0; en)",
        "Opera/9.21 (Windows NT 5.1; U; nl)",
        "Opera/9.21 (Windows NT 5.1; U; pl)",
        "Opera/9.21 (Windows NT 5.1; U; pt-br)",
        "Opera/9.21 (Windows NT 5.1; U; ru)",
        "Opera/9.21 (Windows NT 5.1; U; SV1; MEGAUPLOAD 1.0; ru)",
        "Opera/9.21 (Windows NT 5.2; U; en)",
        "Opera/9.21 (Windows NT 6.0; U; en)",
        "Opera/9.21 (Windows NT 6.0; U; nb)",
        "Opera/9.21 (X11; Linux i686; U; de)",
        "Opera/9.21 (X11; Linux i686; U; en)",
        "Opera/9.21 (X11; Linux i686; U; es-es)",
        "Opera/9.21 (X11; Linux x86_64; U; en)",
        "Opera/9.22 (Windows NT 5.1; U; en)",
        "Opera/9.22 (Windows NT 5.1; U; fr)",
        "Opera/9.22 (Windows NT 5.1; U; pl)",
        "Opera/9.22 (Windows NT 5.1; U; SV1; MEGAUPLOAD 1.0; ru)",
        "Opera/9.22 (Windows NT 5.1; U; SV1; MEGAUPLOAD 2.0; ru)",
        "Opera/9.22 (Windows NT 6.0; U; en)",
        "Opera/9.22 (Windows NT 6.0; U; ru)",
        "Opera/9.22 (X11; Linux i686; U; de)",
        "Opera/9.22 (X11; Linux i686; U; en)",
        "Opera/9.22 (X11; OpenBSD i386; U; en)",
        "Opera/9.23 (Mac OS X; fr)",
        "Opera/9.23 (Mac OS X; ru)",
        "Opera/9.23 (Macintosh; Intel Mac OS X; U; ja)",
        "Opera/9.23 (Nintendo Wii; U; ; 1038-58; Wii Internet Channel/1.0; en)",
        "Opera/9.23 (Windows NT 5.0; U; de)",
        "Opera/9.23 (Windows NT 5.0; U; en)",
        "Opera/9.23 (Windows NT 5.1; U; da)",
        "Opera/9.23 (Windows NT 5.1; U; de)",
        "Opera/9.23 (Windows NT 5.1; U; en)",
        "Opera/9.23 (Windows NT 5.1; U; fi)",
        "Opera/9.23 (Windows NT 5.1; U; it)",
        "Opera/9.23 (Windows NT 5.1; U; ja)",
        "Opera/9.23 (Windows NT 5.1; U; pt)",
        "Opera/9.23 (Windows NT 5.1; U; SV1; MEGAUPLOAD 1.0; ru)",
        "Opera/9.23 (Windows NT 5.1; U; zh-cn)",
        "Opera/9.23 (Windows NT 6.0; U; de)",
        "Opera/9.23 (X11; Linux i686; U; en)",
        "Opera/9.23 (X11; Linux i686; U; es-es)",
        "Opera/9.23 (X11; Linux x86_64; U; en)",
        "Opera/9.24 (Macintosh; PPC Mac OS X; U; en)",
        "Opera/9.24 (Windows NT 5.0; U; ru)",
        "Opera/9.24 (Windows NT 5.1; U; ru)",
        "Opera/9.24 (Windows NT 5.1; U; tr)",
        "Opera/9.24 (X11; Linux i686; U; de)",
        "Opera/9.24 (X11; SunOS i86pc; U; en)",
        "Opera/9.25 (Macintosh; Intel Mac OS X; U; en)",
        "Opera/9.25 (Macintosh; PPC Mac OS X; U; en)",
        "Opera/9.25 (OpenSolaris; U; en)",
        "Opera/9.25 (Windows NT 4.0; U; en)",
        "Opera/9.25 (Windows NT 5.0; U; cs)",
        "Opera/9.25 (Windows NT 5.0; U; en)",
        "Opera/9.25 (Windows NT 5.1; U; de)",
        "Opera/9.25 (Windows NT 5.1; U; lt)",
        "Opera/9.25 (Windows NT 5.1; U; MEGAUPLOAD 1.0; pt-br)",
        "Opera/9.25 (Windows NT 5.1; U; ru)",
        "Opera/9.25 (Windows NT 5.1; U; zh-cn)",
        "Opera/9.25 (Windows NT 5.2; U; en)",
        "Opera/9.25 (Windows NT 6.0; U; en-US)",
        "Opera/9.25 (Windows NT 6.0; U; MEGAUPLOAD 1.0; ru)",
        "Opera/9.25 (Windows NT 6.0; U; ru)",
        "Opera/9.25 (Windows NT 6.0; U; sv)",
        "Opera/9.25 (Windows NT 6.0; U; SV1; MEGAUPLOAD 2.0; ru)",
        "Opera/9.25 (X11; Linux i686; U; en)",
        "Opera/9.25 (X11; Linux i686; U; fr-ca)",
        "Opera/9.25 (X11; Linux i686; U; fr)",
        "Opera/9.26 (Macintosh; PPC Mac OS X; U; en)",
        "Opera/9.26 (Windows NT 5.1; U; de)",
        "Opera/9.26 (Windows NT 5.1; U; MEGAUPLOAD 2.0; en)",
        "Opera/9.26 (Windows NT 5.1; U; nl)",
        "Opera/9.26 (Windows NT 5.1; U; pl)",
        "Opera/9.26 (Windows NT 5.1; U; zh-cn)",
        "Opera/9.27 (Macintosh; Intel Mac OS X; U; sv)",
        "Opera/9.27 (Windows NT 5.1; U; ja)",
        "Opera/9.27 (Windows NT 5.2; U; en)",
        "Opera/9.27 (X11; Linux i686; U; en)",
        "Opera/9.27 (X11; Linux i686; U; fr)",
        "Opera/9.30 (Nintendo Wii; U; ; 2047-7; de)",
        "Opera/9.30 (Nintendo Wii; U; ; 2047-7; fr)",
        "Opera/9.30 (Nintendo Wii; U; ; 2047-7;en)",
        "Opera/9.30 (Nintendo Wii; U; ; 2047-7;es)",
        "Opera/9.30 (Nintendo Wii; U; ; 2047-7;pt-br)",
        "Opera/9.30 (Nintendo Wii; U; ; 2071; Wii Shop Channel/1.0; en)",
        "Opera/9.5 (Windows NT 5.1; U; fr)",
        "Opera/9.5 (Windows NT 6.0; U; en)",
        "Opera/9.50 (Macintosh; Intel Mac OS X; U; de)",
        "Opera/9.50 (Macintosh; Intel Mac OS X; U; en)",
        "Opera/9.50 (Windows NT 5.1; U; es-ES)",
        "Opera/9.50 (Windows NT 5.1; U; it)",
        "Opera/9.50 (Windows NT 5.1; U; nl)",
        "Opera/9.50 (Windows NT 5.1; U; nn)",
        "Opera/9.50 (Windows NT 5.1; U; ru)",
        "Opera/9.50 (Windows NT 5.2; U; it)",
        "Opera/9.50 (X11; Linux i686; U; es-ES)",
        "Opera/9.50 (X11; Linux ppc; U; en)",
        "Opera/9.50 (X11; Linux x86_64; U; nb)",
        "Opera/9.50 (X11; Linux x86_64; U; pl)",
        "Opera/9.51 (Macintosh; Intel Mac OS X; U; en)",
        "Opera/9.51 (Windows NT 5.1; U; da)",
        "Opera/9.51 (Windows NT 5.1; U; en-GB)",
        "Opera/9.51 (Windows NT 5.1; U; en)",
        "Opera/9.51 (Windows NT 5.1; U; es-AR)",
        "Opera/9.51 (Windows NT 5.1; U; es-LA)",
        "Opera/9.51 (Windows NT 5.1; U; fr)",
        "Opera/9.51 (Windows NT 5.1; U; nn)",
        "Opera/9.51 (Windows NT 5.2; U; en)",
        "Opera/9.51 (Windows NT 6.0; U; en)",
        "Opera/9.51 (Windows NT 6.0; U; es)",
        "Opera/9.51 (Windows NT 6.0; U; sv)",
        "Opera/9.51 (X11; Linux i686; U; de)",
        "Opera/9.51 (X11; Linux i686; U; fr)",
        "Opera/9.51 (X11; Linux i686; U; Linux Mint; en)",
        "Opera/9.52 (Macintosh; Intel Mac OS X; U; pt-BR)",
        "Opera/9.52 (Macintosh; Intel Mac OS X; U; pt)",
        "Opera/9.52 (Macintosh; PPC Mac OS X; U; fr)",
        "Opera/9.52 (Macintosh; PPC Mac OS X; U; ja)",
        "Opera/9.52 (Windows NT 5.0; U; en)",
        "Opera/9.52 (Windows NT 5.2; U; ru)",
        "Opera/9.52 (Windows NT 6.0; U; de)",
        "Opera/9.52 (Windows NT 6.0; U; en)",
        "Opera/9.52 (Windows NT 6.0; U; fr)",
        "Opera/9.52 (Windows NT 6.0; U; Opera/9.52 (X11; Linux x86_64; U); en)",
        "Opera/9.52 (X11; Linux i686; U; cs)",
        "Opera/9.52 (X11; Linux i686; U; en)",
        "Opera/9.52 (X11; Linux i686; U; fr)",
        "Opera/9.52 (X11; Linux ppc; U; de)",
        "Opera/9.52 (X11; Linux x86_64; U; en)",
        "Opera/9.52 (X11; Linux x86_64; U; ru)",
        "Opera/9.52 (X11; Linux x86_64; U)",
        "Opera/9.60 (Windows NT 5.0; U; en) Presto/2.1.1",
        "Opera/9.60 (Windows NT 5.1; U; en-GB) Presto/2.1.1",
        "Opera/9.60 (Windows NT 5.1; U; es-ES) Presto/2.1.1",
        "Opera/9.60 (Windows NT 5.1; U; sv) Presto/2.1.1",
        "Opera/9.60 (Windows NT 5.1; U; tr) Presto/2.1.1",
        "Opera/9.60 (Windows NT 6.0; U; bg) Presto/2.1.1",
        "Opera/9.60 (Windows NT 6.0; U; de) Presto/2.1.1",
        "Opera/9.60 (Windows NT 6.0; U; pl) Presto/2.1.1",
        "Opera/9.60 (Windows NT 6.0; U; ru) Presto/2.1.1",
        "Opera/9.60 (Windows NT 6.0; U; uk) Presto/2.1.1",
        "Opera/9.60 (X11; Linux i686; U; en-GB) Presto/2.1.1",
        "Opera/9.60 (X11; Linux i686; U; ru) Presto/2.1.1",
        "Opera/9.60 (X11; Linux x86_64; U)",
        "Opera/9.61 (Macintosh; Intel Mac OS X; U; de) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.1; U; cs) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.1; U; de) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.1; U; en-GB) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.1; U; en) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.1; U; fr) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.1; U; ru) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.1; U; zh-cn) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.1; U; zh-tw) Presto/2.1.1",
        "Opera/9.61 (Windows NT 5.2; U; en) Presto/2.1.1",
        "Opera/9.61 (Windows NT 6.0; U; en) Presto/2.1.1",
        "Opera/9.61 (Windows NT 6.0; U; http://lucideer.com; en-GB) Presto/2.1.1",
        "Opera/9.61 (Windows NT 6.0; U; pt-BR) Presto/2.1.1",
        "Opera/9.61 (Windows NT 6.0; U; ru) Presto/2.1.1",
        "Opera/9.61 (X11; Linux i686; U; de) Presto/2.1.1",
        "Opera/9.61 (X11; Linux i686; U; en) Presto/2.1.1",
        "Opera/9.61 (X11; Linux i686; U; pl) Presto/2.1.1",
        "Opera/9.61 (X11; Linux i686; U; ru) Presto/2.1.1",
        "Opera/9.61 (X11; Linux x86_64; U; fr) Presto/2.1.1",
        "Opera/9.62 (Windows NT 5.1; U; pl) Presto/2.1.1",
        "Opera/9.62 (Windows NT 5.1; U; pt-BR) Presto/2.1.1",
        "Opera/9.62 (Windows NT 5.1; U; ru) Presto/2.1.1",
        "Opera/9.62 (Windows NT 5.1; U; tr) Presto/2.1.1",
        "Opera/9.62 (Windows NT 5.1; U; zh-cn) Presto/2.1.1",
        "Opera/9.62 (Windows NT 5.1; U; zh-tw) Presto/2.1.1",
        "Opera/9.62 (Windows NT 5.2; U; en) Presto/2.1.1",
        "Opera/9.62 (Windows NT 6.0; U; de) Presto/2.1.1",
        "Opera/9.62 (Windows NT 6.0; U; en-GB) Presto/2.1.1",
        "Opera/9.62 (Windows NT 6.0; U; en) Presto/2.1.1",
        "Opera/9.62 (Windows NT 6.0; U; nb) Presto/2.1.1",
        "Opera/9.62 (Windows NT 6.0; U; pl) Presto/2.1.1",
        "Opera/9.62 (Windows NT 6.1; U; de) Presto/2.1.1",
        "Opera/9.62 (Windows NT 6.1; U; en) Presto/2.1.1",
        "Opera/9.62 (X11; Linux i686; U; en) Presto/2.1.1",
        "Opera/9.62 (X11; Linux i686; U; fi) Presto/2.1.1",
        "Opera/9.62 (X11; Linux i686; U; it) Presto/2.1.1",
        "Opera/9.62 (X11; Linux i686; U; Linux Mint; en) Presto/2.1.1",
        "Opera/9.62 (X11; Linux i686; U; pt-BR) Presto/2.1.1",
        "Opera/9.62 (X11; Linux x86_64; U; ru) Presto/2.1.1",
        "Opera/9.63 (Windows NT 5.1; U; pt-BR) Presto/2.1.1",
        "Opera/9.63 (Windows NT 5.2; U; de) Presto/2.1.1",
        "Opera/9.63 (Windows NT 5.2; U; en) Presto/2.1.1",
        "Opera/9.63 (Windows NT 6.0; U; cs) Presto/2.1.1",
        "Opera/9.63 (Windows NT 6.0; U; en) Presto/2.1.1",
        "Opera/9.63 (Windows NT 6.0; U; fr) Presto/2.1.1",
        "Opera/9.63 (Windows NT 6.0; U; nb) Presto/2.1.1",
        "Opera/9.63 (Windows NT 6.0; U; pl) Presto/2.1.1",
        "Opera/9.63 (Windows NT 6.1; U; de) Presto/2.1.1",
        "Opera/9.63 (Windows NT 6.1; U; en) Presto/2.1.1",
        "Opera/9.63 (Windows NT 6.1; U; hu) Presto/2.1.1",
        "Opera/9.63 (X11; FreeBSD 7.1-RELEASE i386; U; en) Presto/2.1.1",
        "Opera/9.63 (X11; Linux i686; U; de) Presto/2.1.1",
        "Opera/9.63 (X11; Linux i686; U; en)",
        "Opera/9.63 (X11; Linux i686; U; nb) Presto/2.1.1",
        "Opera/9.63 (X11; Linux i686; U; ru)",
        "Opera/9.63 (X11; Linux i686; U; ru) Presto/2.1.1",
        "Opera/9.63 (X11; Linux i686)",
        "Opera/9.63 (X11; Linux x86_64; U; cs) Presto/2.1.1",
        "Opera/9.63 (X11; Linux x86_64; U; ru) Presto/2.1.1",
        "Opera/9.64 (Windows NT 6.0; U; pl) Presto/2.1.1",
        "Opera/9.64 (Windows NT 6.0; U; zh-cn) Presto/2.1.1",
        "Opera/9.64 (Windows NT 6.1; U; de) Presto/2.1.1",
        "Opera/9.64 (Windows NT 6.1; U; MRA 5.5 (build 02842); ru) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; da) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; de) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; en) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; Linux Mint; it) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; Linux Mint; nb) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; nb) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; pl) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; sv) Presto/2.1.1",
        "Opera/9.64 (X11; Linux i686; U; tr) Presto/2.1.1",
        "Opera/9.64 (X11; Linux x86_64; U; cs) Presto/2.1.1",
        "Opera/9.64 (X11; Linux x86_64; U; de) Presto/2.1.1",
        "Opera/9.64 (X11; Linux x86_64; U; en-GB) Presto/2.1.1",
        "Opera/9.64 (X11; Linux x86_64; U; en) Presto/2.1.1",
        "Opera/9.64 (X11; Linux x86_64; U; hr) Presto/2.1.1",
        "Opera/9.64 (X11; Linux x86_64; U; pl) Presto/2.1.1",
        "Opera/9.64(Windows NT 5.1; U; en) Presto/2.1.1",
        "Opera/9.70 (Linux i686 ; U; ; en) Presto/2.2.1",
        "Opera/9.70 (Linux i686 ; U; ; en) Presto/2.2.1",
        "Opera/9.70 (Linux i686 ; U; en-us) Presto/2.2.0",
        "Opera/9.70 (Linux i686 ; U; en) Presto/2.2.0",
        "Opera/9.70 (Linux i686 ; U; en) Presto/2.2.1",
        "Opera/9.70 (Linux i686 ; U; zh-cn) Presto/2.2.0",
        "Opera/9.70 (Linux ppc64 ; U; en) Presto/2.2.1",
        "Opera/9.80 (J2ME/MIDP; Opera Mini/5.0 (Windows; U; Windows NT 5.1; en) AppleWebKit/886; U; en) Presto/2.4.15",
        "Opera/9.80 (Linux i686; U; en) Presto/2.5.22 Version/10.51",
        "Opera/9.80 (Macintosh; Intel Mac OS X; U; nl) Presto/2.6.30 Version/10.61",
        "Opera/9.80 (Windows 98; U; de) Presto/2.6.30 Version/10.61",
        "Opera/9.80 (Windows NT 5.1; U; cs) Presto/2.2.15 Version/10.10",
        "Opera/9.80 (Windows NT 5.1; U; de) Presto/2.2.15 Version/10.10",
        "Opera/9.80 (Windows NT 5.1; U; it) Presto/2.7.62 Version/11.00",
        "Opera/9.80 (Windows NT 5.1; U; pl) Presto/2.6.30 Version/10.62",
        "Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.2.15 Version/10.00",
        "Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.5.22 Version/10.50",
        "Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.7.39 Version/11.00",
        "Opera/9.80 (Windows NT 5.1; U; zh-cn) Presto/2.2.15 Version/10.00",
        "Opera/9.80 (Windows NT 5.2; U; en) Presto/2.2.15 Version/10.00",
        "Opera/9.80 (Windows NT 5.2; U; en) Presto/2.6.30 Version/10.63",
        "Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.5.22 Version/10.51",
        "Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.6.30 Version/10.61",
        "Opera/9.80 (Windows NT 5.2; U; zh-cn) Presto/2.6.30 Version/10.63",
        "Opera/9.80 (Windows NT 6.0; U; cs) Presto/2.5.22 Version/10.51",
        "Opera/9.80 (Windows NT 6.0; U; de) Presto/2.2.15 Version/10.00",
        "Opera/9.80 (Windows NT 6.0; U; en) Presto/2.2.15 Version/10.00",
        "Opera/9.80 (Windows NT 6.0; U; en) Presto/2.2.15 Version/10.10",
        "Opera/9.80 (Windows NT 6.0; U; en) Presto/2.7.39 Version/11.00",
        "Opera/9.80 (Windows NT 6.0; U; Gecko/20100115; pl) Presto/2.2.15 Version/10.10",
        "Opera/9.80 (Windows NT 6.0; U; it) Presto/2.6.30 Version/10.61",
        "Opera/9.80 (Windows NT 6.0; U; nl) Presto/2.6.30 Version/10.60",
        "Opera/9.80 (X11; U; Linux i686; en-US; rv:1.9.2.3) Presto/2.2.15 Version/10.10",
        "Opera/9.99 (Windows NT 5.1; U; pl) Presto/9.9.9"
    ]
    return random.choice(userAgentArray)    



def run (action, params=None):
    logga('Run version '+versione)
    commands = {
        'myStream': myStream,
        'wizhd': wizhd,
        'daddy': daddy,
        'wigi': wigi,
        'proData': proData,
        'risolvi': urlsolver,
        'dplay': dplay,
        'dplayLive': dplayLive,
        'mac': macLink,
        'scws': scws,
        'assia': assia,
        'vudeo': vudeo,
        'pulive': pulive,
        'voe': voe,
        'taxi': taxi,
        'scom': scommunity,
        'stape': streamTape,
        'urlsolve': resolveMyUrl,
        'rocktalk': rocktalk
    }

    if action in commands:
        return commands[action](params)
    else:
        raise ValueError('Invalid command: {0}!'.action)
