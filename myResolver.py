versione='1.1.22'
# Module: myResolve
# Author: ElSupremo
# Created on: 10.04.2021
# Last update: 28.07.2022
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
else:
    import urllib as myParse

def logga(mess):
    if debug == "on":
        logging.warning("MANDRA_RESOLVE: "+mess);

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
        headers=headers,
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
    logga('IFRAME: '+iframe_url)

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
    logging.warning('URL: '+linkIframe)
    vUrl = ""
    try:
        page_data2 = requests.get(linkIframe,headers={'user-agent':'iPad','accept':'*/*','referer':refPage}).content

        if PY3:
            page_data2 = page_data2.decode('utf-8')

        video_url = preg_match(page_data2, r'source:\s*"([^"]+)')
        if video_url == "":
            video_url = preg_match(page_data2, r"source:\s*'([^']+)")
        if video_url != "":
            vUrl = video_url + '|User-Agent=Mozilla/5.0&Referer='+linkIframe
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
    page_data = requests.get(parIn,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':'https://daddylive.eu/'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    iframe_url = preg_match(page_data, r'iframe\s*src="([^"]+)')
    logga('IFRAME DADDY: '+iframe_url)
    if "http" in iframe_url:
        page_data2 = requests.get(iframe_url,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':parIn}).content
        if PY3:
            page_data2 = page_data2.decode('utf-8')
        
        iframe_url2 = preg_match(page_data2, r'iframe\s*src="([^"]+)')
        logga('IFRAME DADDY2: '+iframe_url2)
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
    if video_url == "":
        video_url = "https://srv.vhls.ru.com/cdn/premium"+vId+"/tracks-v1a1/mono.m3u8"
    final_url = video_url+"|Referer=https://widevine.licenses4.me/"
    final_url2 = video_url+"|Referer=https://widevine.licenses4.me/ Origin=https://widevine.licenses4.me/"

    

    video_urls.append((final_url, "[COLOR lime]PLAY STREAM "+arrTmp2[0]+"[/COLOR]", "by @MandraKodi", "https://i.imgur.com/8EL6mr3.png"))
    #video_urls.append((final_url2, "[COLOR yellow]PLAY STREAM "+arrTmp2[0]+"[/COLOR]", "by @MandraKodi", "https://i.imgur.com/8EL6mr3.png"))
    """
    if "|" in video_url:
        arrV = video_url.split("|")
        video_urls.append((arrV[0], ""))		
    """
    return video_urls

def GetLSProData(page_in, refe=None):
    import jsunpack

    logga('page_in '+page_in)
    if refe != None:
        logga('REFER '+refe)
    if "hdmario" in page_in:
        logga('HDMARIO')
        fu = requests.get(page_in, headers={'user-agent':'iPad','referer':page_in}).text
        find = re.findall('eval\(function(.+?.+)', fu)[0]
        unpack = jsunpack.unpack(find)
        logga('UNPACK: '+unpack)
        c = re.findall('var src="([^"]*)',unpack)[0]
        logga('URL_MARIO '+c)
        return c

    page_data = requests.get(page_in,headers={'user-agent':'iPad','accept':'*/*','referer':refe}).content

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

    if "wigistream" in src:
        logga('iframe_wigistream_ok ')
    elif "embed" in src:
        logga('iframe_wigistream_ok ')
    elif "buzztv" in src:
        logga('BUZZTV ')
        return GetLSProData(src)
    elif "cloudstream" in src:
        logga('CLOUDSTREAM')
        return GetLSProData(src)
    elif "pepperlive" in src:
        logga('PEPPER')
        return GetLSProData(src)
    elif "hdmario" in src:
        logga('HDMARIO')
        return GetLSProData(src)
    else:
        logga('CALL findM3u8 FUNCTION ')
        return findM3u8(src, page_in)

    fu = requests.get(src, headers={'user-agent':'iPad','referer':page_in}).text
    find = re.findall('eval\(function(.+?.+)', fu)[0]
    unpack = jsunpack.unpack(find)
    c = re.findall('var src="([^"]*)',unpack)[0]
    return c + '|referer=' + src

def wigi(parIn=None):

    if parIn.startswith('http'):
        wigiUrl = parIn
    else:
        #wigiUrl = "https://starlive.xyz/embed.php?id="+parIn
        wigiUrl = "https://starlive.xyz/"+parIn

    video_urls = []
    logga('PAR: '+parIn)
    video_url = GetLSProData(wigiUrl)
    logga('video_url '+video_url)
    video_urls.append((video_url, ""))
    if "|" in video_url:
        arrV = video_url.split("|")
        video_urls.append((arrV[0], ""))		
    return video_urls

def urlsolver(url):
    video_urls = []

    resolvedUrl=get_resolved(url)
    logga('video_resolved_url '+resolvedUrl)
    if (resolvedUrl != url):
        video_urls.append((resolvedUrl, "LINK 1"))
        if "|" in resolvedUrl:
            arrV = resolvedUrl.split("|")
            linkClean=arrV[0]
            logga('video_resolved_cleaned '+linkClean)
            video_urls.append((linkClean, "LINK 2"))		

        return video_urls
    else:
        dialog = xbmcgui.Dialog()
        mess = "Sorry, ResolveUrl does not support this domain"
        dialog.ok("Mandrakodi", mess)
    return url

def resolveMyUrl(url):
    import resolveurl, xbmcvfs
    xxx_plugins_path = 'special://home/addons/script.module.resolveurl.xxx/resources/plugins/'
    if xbmcvfs.exists(xxx_plugins_path):
        resolveurl.add_plugin_dirs(xbmc.translatePath(xxx_plugins_path))
    resolved = ""
    try:
        resolved = resolveurl.resolve(url)
    except:
        pass
    if resolved:
        logging.error("MANDRA URL_SOLVED: "+resolved)
        return resolved
    else:
        return url


def get_resolved(url):
    import xbmcvfs
    
    resolved = daddyFind(url)
    if resolved:
        return resolved
    else:
        logga("NO RESOLVER DADDY")		

    resolved = wizhdFind(url)
    if resolved:
        return resolved
    else:
        logga("NO RESOLVER WIZHD")		

    resolved = assiaFind(url)
    if resolved:
        return resolved
    else:
        logga("NO RESOLVER ASSIA")		

    resolved = GetLSProData(url)
    if resolved:
        return resolved
    else:
        logga("NO RESOLVER DATA")		

    try:
        import resolveurl
    except:
        dialog = xbmcgui.Dialog()
        mess = "Lo script 'script.module.resolveurl' non risulta installato."
        dialog.ok("Mandrakodi", mess)
        return url

    logga("TRY TO RESOLVE: "+url)
    xxx_plugins_path = 'special://home/addons/script.module.resolveurl.xxx/resources/plugins/'
    if xbmcvfs.exists(xxx_plugins_path):
        logging.warning("OK XXX RESOLVER ")
        if sys.version_info[0] > 2:
            xxxp = xbmcvfs.translatePath(xxx_plugins_path)
        else:
            import xbmc
            xxxp = xbmc.translatePath(xxx_plugins_path)
        resolveurl.add_plugin_dirs(xxxp)
    try:
        resolved = resolveurl.resolve(url)
        if resolved:
            logga("OK RESOLVER: "+resolved)
            return resolved
    except Exception as err:
        import traceback
        
        errMsg="ERROR_RESOLVER: {0}".format(err)
        logga(errMsg)
        traceback.print_exc()

    return url

def streamingcommunity(parIn=None):
    import json
    video_urls = []
    url_sito = "https://streamingcommunity.cc/"
    page_video = url_sito + "watch/" + parIn
    page_data = requests.get(page_video,headers={'user-agent':'Mozilla/5.0','accept':'*/*'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    patron=r'<video-player response="(.*?)"'
    dataF = preg_match(page_data, patron)
    #logga("DATA FROM STRCO: "+dataF)
    dataJ = dataF.replace('&quot;','"')
    try:
        arrJ = json.loads(dataJ)
    except Exception as e:
        logga("NO JSON FROM STRCO: "+page_video)
        raise ValueError('NO JSON FROM: '+page_video)

    nm=arrJ["title"]["name"]
    name = "[COLOR lime]"+nm.upper()+"[/COLOR]"
    plot = arrJ["title"]["plot"]
    idVideo = arrJ["video_id"]
    url = url_sito + "videos/master/" + str(idVideo) + "m3u8"
    if "scws_id" in arrJ:
        logga("SCWS: "+str(arrJ["scws_id"]))	
        idVideo = arrJ["scws_id"]
        url = "https://scws.xyz/master/" + str(idVideo)

    def calculateToken(ip_client):
        from time import time
        from base64 import b64encode as b64
        import hashlib
        o = 48
        i = 'Yc8U6r8KjAKAepEA'
        t = int(time() + (3600 * o))
        l = '{}{} {}'.format(t, ip_client, i)
        md5 = hashlib.md5(l.encode())
        s = '?token={}&expires={}'.format(b64(md5.digest()).decode().replace('=', '').replace('+', "-").replace('\\', "_"), t)
        return s + '&n=1'
    
    page_video = "https://scws.xyz/videos/" + str(idVideo)
    page_data = requests.get(page_video,headers={'user-agent':'Mozilla/5.0','accept':'*/*'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    logga('IP_community '+page_data)
    try:
        arrJ2 = json.loads(page_data)
        localIp = arrJ2["client_ip"]
    except:
        logga("NO LOCAL IP")
        localIp = "31.191.12.52"
        pass

    token = calculateToken(localIp)
    code = requests.get(url + token, headers={'user-agent':'Mozilla/5.0','accept':'*/*'}).status_code
    count = 0
    while not code == 200:
        token = calculateToken(localIp)
        code = requests.get(url + token, headers={'user-agent':'Mozilla/5.0','accept':'*/*'}).status_code
        count +=1
        if count == 3:
            logga('END OF TRY. CODE: '+str(code))
            break

    
    video_url = url + token
    logga('video_community '+video_url)
    video_urls.append((video_url, name, plot))

    return video_urls


def scws(parIn=None):
    import json
    video_urls = []
    base="https://streamingcommunity.press/"

    headSCt={'user-agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'}
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

    headSC={'user-agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14',
        'content-type': 'application/json;charset=UTF-8',
        'Referer':refe,
        'x-csrf-token': csrf_token,
        'Origin':base}
    
    url = "https://scws.xyz/master/" + str(parIn)

    def calculateToken(ip_client):
        from time import time
        from base64 import b64encode as b64
        import hashlib

        expires = int(time() + 172800)
        token = b64(hashlib.md5('{}{} Yc8U6r8KjAKAepEA'.format(expires, ip_client).encode('utf-8')).digest()).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')

        s = '?token={}&expires={}&n=1'.format(token, expires)

        #o = 48
        #i = 'Yc8U6r8KjAKAepEA'
        #t = int(time() + (3600 * o))
        #l = '{}{} {}'.format(t, ip_client, i)
        #md5 = hashlib.md5(l.encode())
        #s = '?token={}&expires={}'.format(b64(md5.digest()).decode().replace('=', '').replace('+', "-").replace('\\', "_"), t)
        
        return s + '&n=1'
    
    page_video = "https://scws.xyz/videos/" + str(parIn)
   
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
    pageT = requests.get(url2,headers=headSCt).content
    if PY3:
        pageT = pageT.decode('utf-8')
    logga("MANIFEST: "+pageT)
    
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

                video_urls.append((url3, "[COLOR gold]"+myParse.unquote(titFilm).replace("+", " ")+"[/COLOR] [COLOR blue]("+res+"p)[/COLOR]", "by @mandrakodi"))
            ind += 1
    else:
        video_url = url + token + "|User-Agent=Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14&Referer="+base
        logga('video_community '+video_url)
        video_urls.append((video_url, "[COLOR lime]"+myParse.unquote(titFilm).replace("+", " ")+"[/COLOR]", "by @mandrakodi"))
    
    remoteLog(titFilm)

    return video_urls





def darkIptv(parIn=None):
    video_urls = []
    video_url = "http://temporary.mine.nu:8000/movie/Direct2Movie/r3ow52c4P4/"+parIn
    if "." in parIn:
        video_url = "http://temporary.mine.nu:8000/movie/Direct2Movie/r3ow52c4P4/"+parIn
    else:
        video_url = "http://temporary.mine.nu:8000/Direct2Movie/r3ow52c4P4/"+parIn
    video_urls.append((video_url, ""))
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
    logga(link)

    try:
        link = link.split(" ")[1]
    except:
        pass

    video_urls = []
    video_urls.append((link, ""))
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

    apiUrl2 = domain + "/playback/v3/videoPlaybackInfo/"
    post = {'videoId': parIn, 'deviceInfo': {'adBlocker': False,'drmSupported': True}}
    data2 = session.post(apiUrl2, json=post).content
    data3 = json.loads(data2)
    logga('POST_DPLAY: '+str(data2))

    data = requests.get('https://eu1-prod-direct.discoveryplus.com/playback/videoPlaybackInfo/{}?usePreAuth=true'.format(parIn), headers=myHeaders).content
    logga('RESP_DPLAY: '+str(data))
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

def writeFileLog(strIn, modo):
    home = ''
    if PY3:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
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

def run (action, params=None):
    logga('Run version '+versione)
    commands = {
        'myStream': myStream,
        'wizhd': wizhd,
        'daddy': daddy,
        'wigi': wigi,
        'risolvi': urlsolver,
        'strco': streamingcommunity,
        'dark': darkIptv,
        'dplay': dplay,
        'dplayLive': dplayLive,
        'mac': macLink,
        'scws': scws,
        'assia': assia,
        'stape': streamTape,
        'urlsolve': resolveMyUrl,
        'rocktalk': rocktalk
    }

    if action in commands:
        return commands[action](params)
    else:
        raise ValueError('Invalid command: {0}!'.action)
