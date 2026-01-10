from __future__ import unicode_literals # turns everything to unicode
versione='1.2.195'
# Module: myResolve
# Author: ElSupremo
# Created on: 10.04.2021
# Last update: 10.01.2026
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import re, requests, sys, logging, uuid
import os
import string
import random

from urllib.parse import quote_plus, urlparse, parse_qsl, unquote
from requests import Response

import xbmcgui
import xbmc
import xbmcaddon
import xbmcplugin

from html.parser import HTMLParser
from urllib.request import Request, urlopen



addon_id = 'plugin.video.mandrakodi'
#selfAddon = xbmcaddon.Addon(id=addon_id)
debug = xbmcaddon.Addon(id=addon_id).getSetting("debug")

addon_handle = int(sys.argv[1])

PY3 = sys.version_info[0] == 3
if PY3:
    import urllib.parse as myParse
    import xbmcvfs
else:
    import urllib as myParse


#=================================================
# TOOLS VARI
#=================================================


def logga(mess):
    if debug == "on":
        logging.warning("MANDRA_RESOLVE: "+mess)

def downloadHttpPage(urlIn, **opt):
    import time
    toRet=""
    try:
        head = {
            'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
        }
        s = requests.Session()
        if opt.get('header', None) is not None:
            logga("SET HEADER")
            head = opt['header']
        
        if opt.get('headers', None) is not None:
            logga("SET HEADERS")
            head = opt['headers']
        
        if opt.get('post', None) is not None:
            postData=opt['post']
            logga("POST DATA: "+postData)
            toRet = s.post(urlIn, data=postData, allow_redirects=True, headers=head, timeout=15)
        else:    
            logga("START")
            toRet = s.get(urlIn, headers=head, timeout=45) 
            if opt.get('sleep', None) is not None:
                logga("SLEEP")
                time.sleep(opt['sleep'])
                logga("RE-START")
                s = requests.Session()
                toRet = s.get(urlIn, headers=head, timeout=45)
            logga("END")
        if PY3:
            toRet = toRet.decode('utf-8')
    except:
        pass
    #logga("PAGE:\n"+toRet.text)
    return toRet.text


def find_single_match(data, patron, index=0):
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

def find_multiple_matches(text, pattern):
    return re.findall(pattern, text, re.DOTALL)

def get_domain_from_url(url):
    if PY3:
       import urllib.parse as urlparse       
    else:
       import urlparse                       

    parsed_url = urlparse.urlparse(url)
    try:
        filename = parsed_url.netloc
    except:
        # If it fails it is because the implementation of parsed_url does not recognize the attributes as "path"
        if len(parsed_url) >= 4:
            filename = parsed_url[1]
        else:
            filename = ""

    return filename

def girc(page_data, url, co, size='invisible'):
    """
    Code adapted from https://github.com/vb6rocod/utils/
    Copyright (C) 2019 vb6rocod
    and https://github.com/addon-lab/addon-lab_resolver_Project
    Copyright (C) 2021 ADDON-LAB, KAR10S
    """
    import re, random, string
    
    hdrs = {'Referer': url}
    rurl = 'https://www.google.com/recaptcha/api.js'
    aurl = 'https://www.google.com/recaptcha/api2'
    key = re.search(r"""(?:src="{0}\?.*?render|data-sitekey)=['"]?([^"']+)""".format(rurl), page_data)
    if key:
        key = key.group(1)
        # rurl = '{0}?render={1}'.format(rurl, key)
        page_data1 = downloadHttpPage(rurl, headers=hdrs)
        v = re.findall('releases/([^/]+)', page_data1)[0]
        rdata = {'ar': 1,
                 'k': key,
                 'co': co,
                 'hl': 'it',
                 'v': v,
                 'size': size,
                 'sa': 'submit',
                 'cb': ''.join([random.choice(string.ascii_lowercase + string.digits) for i in range(12)])}
        page_data2 = downloadHttpPage('{0}/anchor?{1}'.format(aurl, myParse.urlencode(rdata)), headers=hdrs)
        rtoken = re.search('recaptcha-token.+?="([^"]+)', page_data2)
        if rtoken:
            rtoken = rtoken.group(1)
        else:
            return ''
        pdata = {'v': v,
                 'reason': 'q',
                 'k': key,
                 'c': rtoken,
                 'sa': '',
                 'co': co}
        hdrs.update({'Referer': aurl})
        page_data3 = downloadHttpPage('{0}/reload?k={1}'.format(aurl, key), post=pdata, headers=hdrs)
        gtoken = re.search('rresp","([^"]+)', page_data3)
        if gtoken:
            return gtoken.group(1)

    return ''

def fix_base64_padding(s):
    # Rimuove spazi o newline eventuali
    s = s.strip()

    # Calcola quante '=' servono
    missing = len(s) % 4

    if missing == 2:
        s += "=="
    elif missing == 3:
        s += "="
    elif missing == 1:
        # Caso raro: stringa malformata
        raise ValueError("Base64 non valido: padding impossibile.")
    
    return s

def skyTV(parIn=None):
    links = []
    requrl = "https://apid.sky.it/vdp/v1/getLivestream?id={}&isMobile=false".format(parIn)
    url = requests.get(requrl).json()["streaming_url"]
    links.append((url, "[COLOR gold]PLAY SKY CH[/COLOR]"))
    return links

def discovery(parIn=None):
    import uuid
    links = []
    host = "https://www.discoveryplus.com"
    deviceId = uuid.uuid4().hex
    logga("URL DEVICEID 4 DISCOVERY: "+deviceId)
    session = requests.Session()
    domain = 'https://' + session.get("https://prod-realmservice.mercury.dnitv.com/realm-config/www.discoveryplus.com%2Fit%2Fepg").json()["domain"]
    urlTk='{}/token?deviceId={}&realm=dplay&shortlived=true'.format(domain, deviceId)
    logga("URL TOKEN DISCOVERY: "+urlTk)
    token = session.get(urlTk).json()['data']['attributes']['token']
    session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': host,
            'Origin': host,
            'Cookie': 'st={}'.format(token),
            'content-type': 'application/json',
            'x-disco-client': 'WEB:UNKNOWN:dplus_us:2.46.0',
            'x-disco-params': 'realm=dplay,siteLookupKey=dplus_it'}
    content = 'channel'
    #post = {content + 'Id': parIn, 'deviceInfo': {'adBlocker': False,'drmSupported': True}}

    post =  {content + 'Id': parIn,
            'deviceInfo': {
                'adBlocker': 'true',
                'drmSupported': 'true',
                'hwDecodingCapabilities': [],
                'screen':{
                    'width':1920,
                    'height':1080
                },
                'player':{
                    'width':1920,
                    'height':1080
                }
            },
            'wisteriaProperties':{
                'advertiser': {
                    'firstPlay': 0,
                    'fwIsLat': 0
                },
                'device':{
                    'browser':{
                        'name': 'chrome',
                        'version': '120.0.6099.225'
                    },
                    'type': 'desktop'
                },
                'platform': 'desktop',
                'product': 'dplus_emea',
                'sessionId': deviceId,
                'streamProvider': {
                    'suspendBeaconing': 0,
                    'hlsVersion': 6,
                    'pingConfig': 1
                }
            }
        }

    url = ""
    dataStr = "NO_DATA"
    try:
        dataStr = session.post('{}/playback/v3/{}PlaybackInfo'.format(domain, content), json=post)
        data = dataStr.json().get('data',{}).get('attributes',{})
        url = data['streaming'][0]['url']
    except:
        logga("ERRORE DISCOVERY: "+dataStr)
        pass
    links.append((url, "[COLOR gold]PLAY DISCOVERY[/COLOR]"))
    return links


def rocktalk(parIn=None):
    from base64 import b64encode, b64decode
    from binascii import a2b_hex
    from Cryptodome.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
    from Cryptodome.Cipher import DES
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Util.Padding import unpad
    import json

    def payload():
        _pubkey = RSA.importKey(
            a2b_hex(
                "30819f300d06092a864886f70d010101050003818d003081890281"
                "8100bfa5514aa0550688ffde568fd95ac9130fcdd8825bdecc46f1"
                "8f6c6b440c3685cc52ca03111509e262dba482d80e977a938493ae"
                "aa716818efe41b84e71a0d84cc64ad902e46dbea2ec61071958826"
                "4093e20afc589685c08f2d2ae70310b92c04f9b4c27d79c8b5dbb9"
                "bd8f2003ab6a251d25f40df08b1c1588a4380a1ce8030203010001"
            )
        )
        _msg = a2b_hex(
            "7b224d4435223a22695757786f45684237686167747948392b58563052513d3d5c6e222c22534"
            "84131223a2242577761737941713841327678435c2f5450594a74434a4a544a66593d5c6e227d"
        )
        cipher = Cipher_PKCS1_v1_5.new(_pubkey)
        ret64=b64encode(cipher.encrypt(_msg))
        logga('JSON PAYLOAD: '+str(ret64))
        return ret64

    logga('TVTAP PARIN: '+parIn)
    links = []
    
    player_user_agent = "mediaPlayerhttp/1.8 (Linux;Android 7.1.2) ExoPlayerLib/2.5.3"
    key = b"98221122"
    user_agent = 'USER-AGENT-tvtap-APP-V2'
    if parIn=="0":
        headers = {
            'User-Agent': user_agent,
            'app-token': '37a6259cc0c1dae299a7866489dff0bd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'taptube.net',
        }
        
        r = requests.post('https://rocktalk.net/tv/index.php?case=get_all_channels', headers=headers, data={"payload": payload(), "username": "603803577"}, timeout=15)
        jj=str(r.json())
        logga('JSON ALL_CH: '+jj.replace("'", '"'))

        jsonText='{"SetViewMode":"503","items":['
        numIt=0
        arrJ = json.loads(jj)
        for ep in arrJ["msg"]["channels"]:
            chId=ep["pk_id"]
            chName=ep["channel_name"]
            chCountry=ep["country"]
            logoCh=ep["img"]
            tit=chName+" ("+chCountry+")"
            if (numIt > 0):
                jsonText = jsonText + ','    
            jsonText = jsonText + '{"title":"[COLOR gold]'+tit+'[/COLOR]","myresolve":"rocktalk@@'+chId+'",'
            jsonText = jsonText + '"thumbnail":"https://rocktalk.net/tv/'+logoCh+'",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"info":"by MandraKodi"}'
            numIt=numIt+1
        
        jsonText = jsonText + "]}"
        logga('JSON-ANY: '+jsonText)
        links.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))

        
        #links.append(("ignoreme", "[COLOR gold]END JOB[/COLOR]"))
        return links

    ch_id = parIn
    
    r = requests.post('https://rocktalk.net/tv/index.php?case=get_channel_link_with_token_latest', 
        headers={"app-token": "37a6259cc0c1dae299a7866489dff0bd"},
        data={"payload": payload(), "channel_id": ch_id, "username": "603803577"},
        timeout=15)

    logga('JSON TVTAP: '+str(r.json()))
    msgRes = r.json()["msg"]
    if msgRes == "Invalid request!":
        links.append(("ignoreme", "[COLOR red]No Link Found[/COLOR]"))
        return links
    
    from pyDes import des, PAD_PKCS5
    
    jch = r.json()["msg"]["channel"][0]
    for stream in jch.keys():
        if "stream" in stream or "chrome_cast" in stream:
            d = des(key)
            link = d.decrypt(b64decode(jch[stream]), padmode=PAD_PKCS5)
    
            if link:
                link = link.decode("utf-8")
                if not link == "dummytext" and link not in links:
                    links.append((link, "[COLOR gold]PLAY STREAM[/COLOR]"))
                    links.append((link+ "|connection=keepalive&Referer=https://rocktalk.net/&User-Agent="+player_user_agent, "[COLOR lime]PLAY STREAM[/COLOR]"))
    
    return links


def livetv(page_url):
    import json
    video_urls = []
    randomUa=getRandomUA()
    logga ("PAGE_LIVETV: "+page_url)

    arrP=page_url.split("webplayer2.php?")
    try:
        newStr=arrP[1]
        arrP1=newStr.split("&")
        if (arrP1[0]=="t=youtube" or arrP1[0]=="t=youtub"):
            codeYT=arrP1[1].split("c=")[1]
            ytp="https://www.youtube.com/watch?v="+codeYT
            logga ("PAGE_YOUTUBE: "+ytp)
            return resolveMyUrl(ytp)
        if (arrP1[0]=="t=alieztv"):
            codeAL=arrP1[1].split("c=")[1]
            alp="https://emb.apl375.me/player/live.php?id="+codeAL+"&w=700&h=480"
            page_data = downloadHttpPage(alp)
            page_data_flat=page_data.replace("\n", "").replace("\r", "").replace("\t", "")
            logga ("HTML_ALP375: "+page_data_flat)
            src = preg_match(page_data, "pl.init\('([^']*)")
            logga ("SRC ==> "+src)
            video_urls.append(("https:"+src, "[COLOR lime]PLAY STREAM AL[/COLOR]", "by @MandraKodi", "https://cdn.livetv822.me/img/minilogo.gif"))
            return video_urls
    except:
        pass
    page_data = downloadHttpPage(page_url)
    page_data_flat=page_data.replace("\n", "").replace("\r", "").replace("\t", "")
    logga ("HTML_LIVETV: "+page_data_flat)
    src = preg_match(page_data, '<iframe  allowFullScreen="true" scrolling=no frameborder="0 "width="700" height="480" src="([^"]*)')
    if src != "":
        arrHost=src.split("/")
        host="https://"+arrHost[2]
        final_url=""
        try:
            logga ("PAGE2_LIVETV: "+src)
            if "topembed.pw" in src:
                extCode=arrHost[-1].replace("ex", "bet")
                logga("topembed code: "+extCode)
                urlTopServer="https://topembed.pw/server_lookup.php?channel_id="+extCode
                serverTop = requests.get(urlTopServer).json()["server_key"]
                logga("topembed server: "+serverTop)
                
                if serverTop=="top1/cdn":
                    final_url= "https://top1.kiko2.ru/top1/cdn/" + extCode + "/mono.m3u8"
                else:
                    final_url= "https://" + serverTop + "new.kiko2.ru/" + serverTop + "/" + extCode + "/mono.m3u8"
            else:
                arrP2=src.split("play?url=")
                try:
                    m3url=arrP2[1]
                    video_urls.append((myParse.unquote(m3url), "[COLOR lime]PLAY STREAM PL[/COLOR]", "by @MandraKodi", "https://cdn.livetv822.me/img/minilogo.gif"))
                    return video_urls
                except Exception as err:
                    import traceback
                    errMsg="ERRORE MANDRAKODI: {0}".format(err)
                    dialog = xbmcgui.Dialog()
                    dialog.ok("Mandrakodi", errMsg)
                if (src.startswith("//")):
                    src="https:"+src
                page_data2 = downloadHttpPage(src)
                logga ("PAGE2_LIVETV_HTML:\n"+page_data2)
                final_url=preg_match(page_data2, "source: '(.*?)'")
                if final_url == "":
                    jsCode=preg_match(page_data2, '<script type="text/javascript" src="(.*?)"')
                    if jsCode != "":
                        #logga ("JSCODE: "+jsCode)
                        arrJs=jsCode.split("/")
                        urlJs="https://"+arrJs[2]+"/player/m/"+arrJs[-1]+"/"+arrJs[-2]
                        #logga ("JSCODE_A: "+urlJs)
                        page_data3 = downloadHttpPage(urlJs)
                        #logga ("PAGE3_LIVETV_HTML:\n"+page_data3)
                        final_url=preg_match(page_data3, "\"file\": '(.*?)'")+"|connection=keepalive&Referer="+page_url+"&User-Agent="+randomUa
                    else:
                        final_url = findM3u8(src, page_url)
        except:
            pass
        if final_url == "" or final_url == src:
            logga ("GetLSProData: "+src)
            final_url = GetLSProData(src)
        last_url=""
        if "|" in final_url:
            last_url=final_url
        else:
            last_url=final_url+"|Referer="+host+"/&Origin="+host+"&User-Agent=iPad"
        
        video_urls.append((last_url, "[COLOR lime]PLAY STREAM[/COLOR]", "by @MandraKodi", "https://cdn.livetv821.me/img/minilogo.gif"))
        video_urls.append((final_url, "[COLOR gold]PLAY STREAM[/COLOR]", "by @MandraKodi", "https://cdn.livetv821.me/img/minilogo.gif"))
    else:
        video_urls.append((page_url, "[COLOR red]NO LINK FOUND[/COLOR]", "by @MandraKodi", "https://cdn.livetv821.me/img/minilogo.gif"))
    return video_urls


def streamsb(page_url):
    import base64
    video_urls = []
    logga ("PAGE_SB: "+page_url)
    data = downloadHttpPage(page_url)
    
    title="VIDEO"
    try:
        title=find_single_match(data, r'<h1 class="(.*?)">(.*?)<\/h1>')[1].replace("Download ", "")
    except:
        pass

    dl_url = 'https://{}/dl?op=download_orig&id={}&mode={}&hash={}'
    
    host = get_domain_from_url(page_url)
    logga ("HOST_SB: "+host)
    
    #sources = find_multiple_matches(data, r'download_video([^"]+)[^\d]+(\d+)p')
    sources = find_multiple_matches(data, r"download_video\('(.*?)','(.*?)','(.*?)'\)")
    
    if sources:
        logga ("OK_SOURCE_SB: "+sources[0][0]+" - "+sources[0][1]+" - "+sources[0][2]) 
        code = sources[0][0]
        mode = "n"
        hash = sources[0][2]
        newUrl=dl_url.format(host, code, mode, hash)
        logga ("NEW_URL_SB: "+newUrl)
        data = downloadHttpPage(newUrl)
        
        captcha = girc(data, 'https://{0}/'.format(host), base64.b64encode('https://{0}:443'.format(host).encode('utf-8')).decode('utf-8').replace('=', ''))
        if captcha:
            logga ("CAPTCHA_SB: "+captcha)
            hash = find_single_match(data, r'"hash" value="([^"]+)')
            logga ("HASH_CAPTCHA_SB: "+hash)
            newUrl2 = dl_url.format(host, code, mode, hash)
            data = downloadHttpPage(newUrl2, post='op=download_orig&id='+code+'&mode='+mode+'&hash='+hash+'&g-recaptcha-response='+captcha, timeout=10, header={'Referer':newUrl})
            media_url = find_single_match(data, r'<a href="http(.*?)" class="(.*?)">')
            if media_url:
                vUrl="http"+str(media_url[0])
                video_urls.append([vUrl+"|Referer="+page_url, "[COLOR lime]PLAY "+title+"[/COLOR]"])
            else:
                logga ("NO_MEDIA_URL:") 
        else:
            logga ("NO_CAPTCHA_SB\n"+data)
            media_url = find_single_match(data, r'<a href="http(.*?)" class="(.*?)">')
            if media_url:
                vUrl="http"+str(media_url[0])
                video_urls.append([vUrl+"|Referer="+page_url, "[COLOR gold]PLAY "+title+"[/COLOR]"])
    else:
       video_urls.append(["", "[COLOR red]NO LINK FOUND[/COLOR]"])
       logga ("NO_SOURCE_SB: \n") 
    return video_urls



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
    randomUa=getRandomUA()
    logga('CALL: '+parIn)
    page_data = requests.get(parIn,headers={'user-agent':randomUa,'accept':'*/*','Referer':'http://wizhdsports.net/'}).content
    if PY3:
        try:
            page_data = page_data.decode('utf-8')
        except:
            page_data = page_data.decode('latin1')

    iframe_url = preg_match(page_data, r'iframe\s*src="([^"]+)')
    logga('IFRAME WIZ: '+iframe_url)
    if iframe_url.startswith("//"):
        iframe_url="https:"+iframe_url
    if "embed" in iframe_url:
        logga("CALL proData")
        vUrl = GetLSProData(iframe_url, parIn)+"|connection=keepalive&Referer="+parIn+"&User-Agent="+randomUa
    else:
        vUrl = findM3u8(iframe_url, parIn)
    return vUrl
def msgBox(mess):
    dialog = xbmcgui.Dialog()
    dialog.ok("MandraKodi", mess)

def testDns(parIn=""):
    import time
    dns1 = xbmc.getInfoLabel('Network.DNS1Address')
    dns2 = xbmc.getInfoLabel('Network.DNS2Address')
    video_urls = []
    
    logga('CALL DNS TEST '+parIn)
    randomUa=getRandomUA()
    testUrl="https://daddylivestream.com/embed/stream-877.php"
    head={'user-agent':randomUa,'Content-Type':'application/x-www-form-urlencoded','Referer':'https://daddylivestream.com/'}
    resolve="daddyCode@@877"
    if parIn=="StrCom":
        sc_url="https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/data/cs_url.txt"
        scUrl=makeRequest(sc_url)
        testUrl=scUrl.replace("\n", "")+"it/iframe/4474-febbre-da-cavallo"
        head={'user-agent':randomUa}
        resolve="scws2@@4474-febbre-da-cavallo"
    page_data = ""
    time.sleep(2)
    ret="[COLOR lime]TEST DNS: OK[/COLOR]"
    thumb="https://upload.wikimedia.org/wikipedia/commons/f/fb/2000px-ok_x_nuvola_green.png"
    try:
        logga('URL DNS TEST '+testUrl)
        currSess = requests.Session()
        page_data1 = currSess.get(testUrl, headers=head)
        page_data = page_data1.content
        
        if (page_data1.status_code != 200):
            ret="[COLOR red]ERRORE DNS[/COLOR] [COLOR gold]("+str(page_data1.status_code)+")[/COLOR]"
            thumb="https://icon-library.com/images/error-icon-transparent/error-icon-transparent-24.jpg"
        else:
            if PY3:
                try:
                    page_data = page_data.decode('utf-8')
                except:
                    page_data = page_data.decode('latin-1')
           
            iframe_url = preg_match(page_data, r'iframe\s*src="([^"]+)')
            if parIn=="StrCom":
                iframe_url = preg_match(page_data, r'src="(.*?)"')
            if (iframe_url==""):
                ret="[COLOR red]DNS ERRORS[/COLOR]"
                thumb="https://icon-library.com/images/error-icon-transparent/error-icon-transparent-24.jpg"
    except Exception as err:
        import traceback
        
        #errMsg="ERROR_MK2: {0}".format(err)
        #msgBox(errMsg)
        traceback.print_exc()
        ret="[COLOR red]ERRORE REQUEST[/COLOR]"
        thumb="https://icon-library.com/images/error-icon-transparent/error-icon-transparent-24.jpg"
    
    dns1 = xbmc.getInfoLabel('Network.DNS1Address')
    dns2 = xbmc.getInfoLabel('Network.DNS2Address')

    ret += "[COLOR yellow] ["+dns1+" - "+dns2+"][/COLOR]"

    jsonText='{"SetViewMode":"51","items":['
    jsonText = jsonText + '{"title":"'+ret+'","myresolve":"'+ resolve+'",'
    jsonText = jsonText + '"thumbnail":"'+thumb+'",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"}'
    jsonText = jsonText + "]}"
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    
    return video_urls

def markky(parIn):
    video_urls = []
    vUrl = ""
    logga('CALL NOPAY FOR: '+parIn)
    randomUa=getRandomUA()
    head={'user-agent':randomUa,'Content-Type':'application/x-www-form-urlencoded','Referer':'https://markkystreams.com/'}
    page_data = ""
    
    try:
        currSess = requests.Session()
        page_data = currSess.get(parIn,headers=head).content
    except:
        video_urls.append(("ignoreme", "[COLOR red]REQUEST ERROR[/COLOR]", "ERROR", "https://icon-library.com/images/error-icon-transparent/error-icon-transparent-24.jpg"))
        return video_urls
    if PY3:
        try:
            page_data = page_data.decode('utf-8')
        except:
            page_data = page_data.decode('latin1')
    
    logga("page_soloper "+page_data)
    url = preg_match(page_data, r'source: "(.*?)"')
    video_urls.append((url+"|connection=keepalive&verifypeer=false&Referer="+parIn, "[COLOR gold]PLAY STREAM[/COLOR]", "PLAY STREAM", "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
    return video_urls

def nopay(parIn):
    import time
    video_urls = []
    vUrl = ""
    logga('CALL NOPAY FOR: '+parIn)
    randomUa=getRandomUA()
    head={'user-agent':randomUa,'Content-Type':'application/x-www-form-urlencoded','Referer':'https://amstaff.city/index.php'}
    page_data = ""
    
    try:
        currSess = requests.Session()
        p=currSess.get("https://amstaff.city/index.php")
        time.sleep(1)
        indexP = currSess.post("https://amstaff.city/index.php", data="password=equino", headers=head)
        time.sleep(1)
        page_data = currSess.get(parIn,headers=head).content
    except:
        video_urls.append(("ignoreme", "[COLOR red]REQUEST ERROR[/COLOR]", "ERROR", "https://icon-library.com/images/error-icon-transparent/error-icon-transparent-24.jpg"))
        return video_urls
    if PY3:
        try:
            page_data = page_data.decode('utf-8')
        except:
            page_data = page_data.decode('latin1')
    
    logga("page_soloper "+page_data)
    iframe_url = preg_match(page_data, r"iframe\s*src='([^']+)")
    
    logga('IFRAME NOPAY: '+iframe_url)
    if iframe_url == "":
        iframe_url = preg_match(page_data, r'iframe\s*src="([^"]+)')
        logga('IFRAME_2 NOPAY: '+iframe_url)

    if "olalivehdplay.ru" in iframe_url:
        mpdUrl="https://asdfasdft.hlsjs.ru/fls/cdn/"+iframe_url.split("=")[-1]+"/index.m3u8|connection=keepalive&verifypeer=false&Referer=https:"+iframe_url+"&User-Agent="+randomUa
        video_urls.append((mpdUrl, "[COLOR lime]PLAY VIDEO[/COLOR]", "PLAY STREAM", "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
        return video_urls

    if (iframe_url.startswith("mix.php") or iframe_url.startswith("italia.php")):
        mpdUrl=iframe_url.split("#")[1]+"|connection=keepalive&verifypeer=false&Referer="+parIn+"&User-Agent="+randomUa
        video_urls.append((mpdUrl, "[COLOR lime]PLAY STREAM[/COLOR]", "PLAY STREAM", "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
        mpdUrl=iframe_url.split("#")[1]
        video_urls.append((mpdUrl, "[COLOR gold]PLAY EXTERNAL[/COLOR]", "PLAY STREAM", "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
        return video_urls
    
    if (iframe_url.startswith("hls.php")):
        mpdUrl=iframe_url.split("#")[1]+"|connection=keepalive&verifypeer=false&Referer="+parIn+"&User-Agent="+randomUa
        video_urls.append((mpdUrl, "[COLOR lime]PLAY STREAM[/COLOR]", "PLAY STREAM", "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
        mpdUrl=iframe_url.split("#")[1]
        video_urls.append((mpdUrl, "[COLOR gold]PLAY EXTERNAL[/COLOR]", "PLAY STREAM", "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
        return video_urls
    
    if iframe_url.startswith("chrome-extension"):
        arrV = iframe_url.split("#")
        video_urls.append((arrV[1], "[COLOR lime]PLAY STREAM[/COLOR]"))
        return video_urls

    if (iframe_url.startswith("https")):
        newPage=iframe_url 
    else:
        newPage="https:"+iframe_url 

    if "sportsonline" in newPage:
        return proData(newPage)
    
    if "daddylivehd.sx" in newPage or "dlhd.sx" in newPage:
        jsonText='{"SetViewMode":"503","items":['
        jsonText = jsonText + '{"title":"[COLOR lime]FIND DADDY VIDEO[/COLOR]","myresolve":"daddy@@'+newPage+'",'
        jsonText = jsonText + '"thumbnail":"https://techvig.net/wp-content/uploads/2022/07/Daddylive-Alternative-2022.png",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"by MandraKodi"}'
        jsonText = jsonText + "]}"
        video_urls.append((jsonText, "FIND VIDEO", "No info", "noThumb", "json"))
        return video_urls
    
    if "projectlive.info" in newPage:
        return pepper(newPage)
    
    if "tutele1.net" in newPage:
        logga("CALL proData 4 tutele1")
        vUrl = GetLSProData(newPage, parIn)
        final_url = vUrl + "|connection=keepalive&verifypeer=false&Referer="+newPage+"&User-Agent="+randomUa
        video_urls.append((final_url, "[COLOR lime]PLAY STREAM[/COLOR]", "PLAY: "+vUrl, "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
        return video_urls
    
    if "embed" in newPage:
        logga("CALL proData")
        vUrl = GetLSProData(newPage, parIn)
        final_url = vUrl + "|connection=keepalive&verifypeer=false&Referer="+newPage+"&User-Agent="+randomUa
        video_urls.append((final_url, "[COLOR lime]PLAY STREAM[/COLOR]", "PLAY: "+vUrl, "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
        return video_urls
    
    try:
        new_page_data = currSess.get(newPage,headers={'user-agent':randomUa,'accept':'*/*','Referer':parIn}, verify=False).content
    except:
        video_urls.append(("ignoreme", "[COLOR red]REQUEST ERROR[/COLOR]", "ERROR", "https://icon-library.com/images/error-icon-transparent/error-icon-transparent-24.jpg"))
        return video_urls
    if PY3:
        try:
            new_page_data = new_page_data.decode('utf-8')
        except:
            new_page_data = new_page_data.decode('latin1')

    video_url = preg_match(new_page_data, r'source:\s*"([^"]+)')
    if video_url == "":
        video_url = preg_match(new_page_data, r"source:\s*'([^']+)")
    if video_url == "":
        express1 = r"source:'(.*?)'"
        video_url = preg_match(new_page_data, express1)
    
    if video_url != "":
        vUrl = video_url + '|connection=keepalive&User-Agent='+myParse.quote(randomUa)+'&Referer='+newPage
    logga('video_url '+vUrl)

    final_url = vUrl
    video_urls.append((final_url, "[COLOR lime]PLAY STREAM[/COLOR]", "PLAY: "+vUrl, "https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png"))
    return video_urls

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
    import time
    vUrl = ""
    ua = getRandomUA
    try:
        headers = {
            'user-agent': ua
        }
        s = requests.Session()
        r = s.get(linkIframe, headers=headers) 

        headers = {
            'user-agent': ua,
            'referer': refPage
        }
        time.sleep(2)
        s = requests.Session()
        page_data2 = s.get(linkIframe,headers=headers).content

        if PY3:
            try:
                page_data2 = page_data2.decode('utf-8')
            except:
                page_data2 = page_data2.decode('latin1')

        
        
        video_url = preg_match(page_data2, r'source:\s*"([^"]+)')
        if video_url == "":
            video_url = preg_match(page_data2, r"source:\s*'([^']+)")
        if video_url == "":
            express1 = r'file:"(.*?)"'
            video_url = preg_match(page_data2, express1)
        if video_url != "":
            vUrl = video_url + '|connection=keepalive&User-Agent='+myParse.quote(ua)+'&Referer='+linkIframe
        logga('video_url '+vUrl)

    except:
        pass

    return vUrl

def assiaFind(parIn):
    logga('ASSIA_PAR: '+parIn)
    randomUa=getRandomUA()
    page_data = requests.get(parIn,headers={'user-agent':randomUa,'accept':'*/*','Referer':'http://assia1.tv/'}).content
    if PY3:
        try:
            page_data = page_data.decode('utf-8')
        except:
            page_data = page_data.decode('latin1')
    video_url = preg_match(page_data, "source: '(.*?)'")
    
    logga('video_url '+video_url)
    return video_url

def assia(parIn=None):
    video_urls = []
    randomUa=getRandomUA()
    video_url = assiaFind(parIn) + "|connection=keepalive&Referer=http://assia1.tv/&User-Agent="+randomUa
    video_urls.append((video_url, ""))
    if "|" in video_url:
        arrV = video_url.split("|")
        video_urls.append((arrV[0], ""))		
    return video_urls

def mixdrop(page_url):
    import jsunpack, ast
    logga("url=" + page_url)
    video_urls = []
    # data = httptools.downloadpage(page_url).data
    ua='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
    data  = downloadHttpPage(page_url, headers={'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36','referer':page_url})
    logga("mixdrop: " + data)
    packed = preg_match(data, r'(eval.*?)</script>')
    unpacked = jsunpack.unpack(packed)
    list_vars=re.findall(r'MDCore\.\w+\s*=\s*"([^"]+)"', unpacked, re.DOTALL)
    for var in list_vars:
        if '.mp4' in var:
            media_url = var
            break
        else:
            media_url = ''
    if not media_url.startswith('http'):
        media_url = 'http:%s' % media_url
    
    video_urls.append((media_url+"|Referer=https://mixdrop.my/&Origin=https://mixdrop.my&User-Agent="+ua, "[COLOR lime]PLAY STREAM [/COLOR]", "PLAY: MIXDROP", "https://www.businessmagazine.org/wp-content/uploads/2023/05/Daddylive-Alternative-2022.png"))
    return video_urls

def daddyFind(parIn):
    video_url = ""
    page_data = requests.get(parIn,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':'https://daddylivestream.com/'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    iframe_url = preg_match(page_data, r'iframe\s*src="([^"]+)')
    logga('IFRAME DADDY: '+iframe_url)
    if iframe_url.endswith(".mp4"):
        video_url = iframe_url
        return video_url
    if iframe_url.startswith("http"):
        page_data2 = requests.get(iframe_url.replace("caq21harderv991gpluralplay", "forcedtoplay"),headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':parIn}).content
        if PY3:
            page_data2 = page_data2.decode('utf-8')
        
        iframe_url2 = preg_match(page_data2, r'iframe\s*src="([^"]+)')
        logga('IFRAME DADDY2: '+iframe_url2)
        if iframe_url2=="":
            video_url = preg_match(page_data2.replace('//source:','//source_no:'), "source:'(.*?)'")
            logga('VIDEO DADDY2: '+video_url)
            
        if "http" in iframe_url2:
            page_data3 = requests.get(iframe_url2,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':'https://widevine.licenses4.me/'}).content
            if PY3:
                page_data3 = page_data3.decode('utf-8')
            writeFileLog("DADDY_PAGE\n"+page_data3, "w+")
            video_url = preg_match(page_data3, "Clappr.Player[\w\W]*?.source:'(.*?)'")
            vt = video_url.split("?auth")
            video_url = vt[0]

    return video_url

def antenaCode(codeIn=None):
    import re
    video_urls = []
    randomUa="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36"
    randomUa="Mozilla/5.0 (iPad; CPU OS 133 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    link="https://webufffit.mizhls.ru/lb/prima"+codeIn+"/index.m3u8"
    refe="https://1qwebplay.xyz/"
    origin="https://1qwebplay.xyz"
    
    final_url=link+"|Referer="+refe+"&Origin="+origin+"&Connection=keep-alive&User-Agent="+randomUa
        
    video_urls.append((final_url, "[COLOR lime]PLAY STREAM "+codeIn+"[/COLOR]", "PLAY: "+codeIn, "https://www.businessmagazine.org/wp-content/uploads/2023/05/Daddylive-Alternative-2022.png"))
    return video_urls

def huhu(parIn=None):
    link="https://huhu.to/play/"+parIn+"/index.m3u8"
    liz = xbmcgui.ListItem(path=link, offscreen=True)
    liz.setContentLookup(False)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setMimeType("application/x-mpegURL")
    liz.setProperty('inputstream.adaptive.file_type', 'hls')
    ua="Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) QtWebEngine/5.9.7 Chrome/56.0.2924.122 Safari/537.36 Sky_STB_ST412_2018/1.0.0 (Sky, EM150UK,)"
    host="https://huhu.to"
    liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host)
    liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host)
    return liz
        
def sky(parIn=None):
    link="https://calcionew.kiko2.ru/calcio/calcioX2"+parIn+"/mono.m3u8"
    liz = xbmcgui.ListItem(path=link, offscreen=True)
    liz.setContentLookup(False)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setMimeType("application/x-mpegURL")
    liz.setProperty('inputstream.adaptive.file_type', 'hls')
    ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/116.0.0.0"
    host="https://4kwebplay.xyz"
    liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host)
    liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host)
    return liz
        
def daddyPremium(codeIn=None):
    import re, json
    video_urls = []
    randomUa="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 OPR/118.0.0.0"
    headers = {
        'user-agent': randomUa
    }
    s = requests.Session()
    urlSrv="https://dokoplay.xyz/server_lookup.php?channel_id=premium"+codeIn
    dataJson = s.get(urlSrv, headers=headers)
    arrJ = json.loads(dataJson.text)
    server=arrJ["server_key"]
    logga("DADDY_PREMIUM SERVER "+server)
    link="https://"+server+"new.kiko2.ru/"+server+"/premium"+codeIn+"/mono.m3u8"
    
    liz = xbmcgui.ListItem(path=link, offscreen=True)
    liz.setContentLookup(False)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setMimeType("application/x-mpegURL")
    liz.setProperty('inputstream.adaptive.file_type', 'hls')
    ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0"
    host="https://dokoplay.xyz"
    liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host)
    liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host)
    return liz
        

def antena(parIn=None):
    img="https://static.vecteezy.com/system/resources/previews/018/842/688/non_2x/realistic-play-button-video-player-and-streaming-icon-live-stream-3d-render-illustration-free-png.png"
    video_urls = []
    logga('PAR_ANTENA: '+parIn)
    page_data = requests.get(parIn,headers={'user-agent':'Mozilla/5.0','accept':'*/*','Referer':'https://antenasports.ru/'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    iframe_url = preg_match(page_data, r'iframe\s*src="([^"]+)')
    logga('IFRAME ANTENA: '+iframe_url)
    
    arrL=iframe_url.split("=")
    idCh=arrL[1]
    logga('IDCH ANTENA: '+idCh)
    
    randomUa="Mozilla/5.0 (iPad; CPU OS 133 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    link="https://webufffit.mizhls.ru/lb/"+idCh+"/index.m3u8"
    refe="https://1qwebplay.xyz/"
    origin="https://1qwebplay.xyz"
    
    final_url=link+"|Referer="+refe+"&Origin="+origin+"&Connection=keep-alive&User-Agent="+randomUa
    
    liz = xbmcgui.ListItem('AntenaSport', path=final_url)
    liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
    liz.setMimeType('application/x-mpegURL')
    liz.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
    liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
    timeShift = xbmcaddon.Addon(id=addon_id).getSetting("urlAppo4")
    if timeShift != "no_time_shift":
        liz.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
    
    
    return liz

def ffmpeg(link=None):
    randomUa="Mozilla/5.0 (iPad; CPU OS 133 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    arrT=link.split("/")
    
    refe=arrT[0]+"//"+arrT[2]+"/"
    origin=arrT[0]+"//"+arrT[2]
    if "|" in link:
        final_url=link
    else:    
        final_url=link+"|Referer="+refe+"&Origin="+origin+"&Connection=keep-alive&User-Agent="+randomUa
    
    liz = xbmcgui.ListItem('FfMpeg', path=final_url)
    liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
    liz.setMimeType('application/x-mpegURL')
    liz.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
    liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
    timeShift = xbmcaddon.Addon(id=addon_id).getSetting("urlAppo4")
    if timeShift != "no_time_shift":
        liz.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
    
    
    return liz

def ffmpeg_noRef(link=None):
    liz = xbmcgui.ListItem('FfMpeg', path=link)
    liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
    liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
    if "|" in link:
        arrL=link.split("|")
        ref=arrL[1]
        liz.setProperty('inputstream.ffmpegdirect.stream_headers', ref)
    
    timeShift = xbmcaddon.Addon(id=addon_id).getSetting("urlAppo4")
    if timeShift != "no_time_shift":
        liz.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
    
    
    return liz

def koolto(parIn=None):
    video_urls = []
    logga('PAR_KOOL: '+parIn)
    final_url = "https://www.kool.to/play/"+parIn+"/index.m3u8|Referer=https://www.kool.to/&Origin=https://www.kool.to&Connection=keep-alive&User-Agent=ipad"
    video_urls.append((final_url, "[COLOR lime]PLAY STREAM [/COLOR]", "by @MandraKodi", "https://i.imgur.com/8EL6mr3.png"))
    
    final_url = "https://oha.to/play/"+parIn+"/index.m3u8|Referer=https://oha.to/&Origin=https://oha.to&Connection=keep-alive&User-Agent=ipad"
    video_urls.append((final_url, "[COLOR gold]PLAY STREAM [/COLOR]", "by @MandraKodi", "https://i.imgur.com/8EL6mr3.png"))
    
    final_url = "https://vavoo.to/play/"+parIn+"/index.m3u8|Referer=https://vavoo.to/&Origin=https://vavoo.to&Connection=keep-alive&User-Agent=ipad"
    video_urls.append((final_url, "[COLOR blue]PLAY STREAM [/COLOR]", "by @MandraKodi", "https://i.imgur.com/8EL6mr3.png"))
    
    final_url = "https://huhu.to/play/"+parIn+"/index.m3u8|Referer=https://huhu.to/&Origin=https://huhu.to&Connection=keep-alive&User-Agent=ipad"
    video_urls.append((final_url, "[COLOR orange]PLAY STREAM [/COLOR]", "by @MandraKodi", "https://i.imgur.com/8EL6mr3.png"))
    
    return video_urls

def daddy(parIn=None):
    video_urls = []
    logga('PAR_DADDY: '+parIn)
    video_url = daddyFind(parIn)
    logga('URL DADDYS: '+video_url)
    tito = "DADDY"
    refe = parIn
    try:
        arrTmp = parIn.split("stream-")
        arrTmp2 = arrTmp[1].split(".")
        vId = arrTmp2[0]
        tito = vId
        refe = "https://weblivehdplay.ru/premiumtv/daddyhd.php?id="+vId+"&Origin=https://weblivehdplay.ru/premiumtv/daddyhd.php?id="+vId
        if video_url == "":
            return daddyCode(vId)
    except:
        pass

    randomUa=getRandomUA()
    ip64="MTUxLjI1LjIzMS43MQ=="
    final_url = video_url + "?auth="+ip64+"|Keep-Alive=true&Referer="+refe+"&User-Agent="+randomUa
    

    video_urls.append((final_url, "[COLOR lime]PLAY STREAM "+tito+"[/COLOR]", "by @MandraKodi", "https://i.imgur.com/8EL6mr3.png"))
    
    return video_urls



def daddyCode(codeIn=None):
    import re, json, base64
    video_urls = []

    dadUrl="https://dlhd.dad/watch/stream-"+codeIn+".php"
    m3u8=resolve_link(codeIn)

    jsonText='{"SetViewMode":"50","items":['
    jsonText = jsonText + '{"title":"[COLOR lime]PLAY STREAM '+codeIn+'[/COLOR] [COLOR gold](DIRECT)[/COLOR]","link":"'+m3u8+'",'
    jsonText = jsonText + '"thumbnail":"https://i.imgur.com/8EL6mr3.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"},'
    jsonText = jsonText + '{"title":"[COLOR orange]PLAY STREAM '+codeIn+'[/COLOR] [COLOR gold](FFMPEG)[/COLOR]","myresolve":"ffmpeg_noRef@@'+m3u8+'",'
    #jsonText = jsonText + '{"title":"[COLOR orange]PLAY STREAM '+codeIn+'[/COLOR] [COLOR gold](FFMPEG)[/COLOR]","myresolve":"daddy@@https://dlhd.so/embed/stream-'+codeIn+'.php",'
    jsonText = jsonText + '"thumbnail":"https://i.imgur.com/8EL6mr3.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"}'
    
   
    
    jsonText = jsonText + "]}"
    logga('JSON-DADDY: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    
    return video_urls


    randomUa="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0"
    #randomUa=getRandomUA()
    headers = {
        'user-agent': randomUa,
        'referer': "https://dlhd.dad/"
    }
    s = requests.Session()
    
    #urlSrv="https://dlhd.dad/stream/stream-"+codeIn+".php"
    #fuSrv = s.get(urlSrv, headers=headers, verify=False)
    #urlAuth = re.findall('<iframe src="(.*?)"', fuSrv.text)[0]
    #logga("SERVER_AUTH_DADDY: "+urlAuth)
    #arrAuth=urlAuth.split("/")
    #hostAuth=arrAuth[2]
    hostAuth="epicplayplay.cfd"
    urlAuth="https://"+hostAuth+"/premiumtv/daddyhd.php?id="+codeIn
    
    fu = s.get(urlAuth, headers=headers)
    logga ("AUTH_PAGE: "+fu.text)

    bundle64 = re.findall('const IJXX="(.*?)"', fu.text)[0]
    logga("BUNDLE_DADDY: "+bundle64)
    bundle=base64.b64decode(bundle64).decode("utf-8")
    arrAuth=json.loads(bundle)
    authTs64 = arrAuth["b_ts"]
    authRnd64 = arrAuth["b_rnd"]
    authSig64 = arrAuth["b_sig"]

    authTs = base64.b64decode(authTs64).decode("utf-8")
    authRnd = base64.b64decode(authRnd64).decode("utf-8")
    authSig = base64.b64decode(authSig64).decode("utf-8")
    
    sigHt=re.findall('src="https://security.giokko.ru/secure.php(.*?)"', fu.text)[0]
    logga("DADDY NEW_URL "+sigHt)
    arrSig=sigHt.split("&sig=")
    authSig=arrSig[1]

    headers = {
        'user-agent': randomUa,
        'referer': "https://"+hostAuth+"/",
        'origin': "https://"+hostAuth
    }
    urlAuth="https://top2new.giokko.ru/auth.php?channel_id=premium"+codeIn+"&ts="+authTs+"&rnd="+authRnd+"&sig="+authSig
    urlAuth="https://security.giokko.ru/secure.php"+sigHt
    
    dataJ2 = s.get(urlAuth, headers=headers)
    logga("DADDY AUTH "+urlAuth+"\n"+dataJ2.text)
    
    urlSrv="https://"+hostAuth+"/server_lookup.php?channel_id=premium"+codeIn

    dataJson = s.get(urlSrv, headers=headers)
    logga("DADDY JSON "+dataJson.text)
    arrJ = json.loads(dataJson.text)
    server=arrJ["server_key"]
    logga("DADDY_CODE SERVER "+server)
    link="https://"+server+"new.giokko.ru/"+server+"/premium"+codeIn+"/mono.m3u8"
    
    refe="https://"+hostAuth+"/"
    origin="https://"+hostAuth
    
    
    final_url=link+"|Referer="+refe+"&Origin="+origin+"&Connection=Keep-Alive&User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0"
    

    jsonText='{"SetViewMode":"50","server":"'+server+'","items":['
    jsonText = jsonText + '{"title":"[COLOR lime]PLAY STREAM '+codeIn+'[/COLOR] [COLOR gold](DIRECT)[/COLOR]","link":"'+final_url+'",'
    jsonText = jsonText + '"thumbnail":"https://i.imgur.com/8EL6mr3.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"},'
    jsonText = jsonText + '{"title":"[COLOR orange]PLAY STREAM '+codeIn+'[/COLOR] [COLOR gold](FFMPEG)[/COLOR]","myresolve":"ffmpeg_noRef@@'+final_url+'",'
    #jsonText = jsonText + '{"title":"[COLOR orange]PLAY STREAM '+codeIn+'[/COLOR] [COLOR gold](FFMPEG)[/COLOR]","myresolve":"daddy@@https://dlhd.so/embed/stream-'+codeIn+'.php",'
    jsonText = jsonText + '"thumbnail":"https://i.imgur.com/8EL6mr3.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"}'
    
   
    
    jsonText = jsonText + "]}"
    logga('JSON-DADDY: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    
    return video_urls

def gdplayer(parIn):
    import json
    video_urls = []
    url="https://en.freewatchtv.top/live-tv/"+parIn
    response = requests.get(url)
    logga ("GDPLAYER_PAGE: "+url+"\n"+response.text)
    page = response.text.replace("\n", "").replace("\r", "").replace("\t", "")
    match = re.search(r'data-src="https:\/\/ava\.karmakurama\.com\/\?id=(.*?)"', page, re.IGNORECASE)
    daddyC="000"
    try:
        daddyC=match.group(1).strip()
    except:
        match1 = re.search(r'"drm":{"clearkey":{"(.*?)":', page, re.IGNORECASE)
        try:
            parIn=parIn+"-"+match1.group(1).strip()
        except:
            pass
        pass    
    logga ("GDPLAYER_CODE: "+daddyC)
    if daddyC=="000":
        video_urls.append(("ignoreMe", "[COLOR orange]No Link Found for "+parIn+"[/COLOR]" , "NO LINK ", "https://clipart-library.com/image_gallery2/Television-Free-Download-PNG.png"))
        return video_urls
    jj=daddyCode(daddyC)
    for linkTmp in jj:
        newList=list(linkTmp)
        newLink=newList[0]
        #logga("JJSON: "+newLink)
        arr_t = json.loads(newLink)
        server=arr_t["server"]
        refe="https://en.freewatchtv.top"
        link="https://ava.karmakurama.com/"+server+"/premium"+daddyC+"/mono.m3u8|Referer="+refe+"/&Origin="+refe+"&User-Agent=iPad"
        video_urls.append((link, "[COLOR lime]Play Stream "+daddyC+"[/COLOR]" , "PLAY VIDEO ", "https://clipart-library.com/image_gallery2/Television-Free-Download-PNG.png"))
        return video_urls


def get_tmdb_video(tmdb_id="926899"):
    import json
    to_ret = "ignoreMe"
    url = "https://vixsrc.to/movie/"+tmdb_id+"/?lang=it"
    
    try:
        response = requests.get(url)
        page = response.text.replace("\n", "").replace("\r", "").replace("\t", "")
        logga ("TMDB_PAGE: "+page)
        match = re.search(r'window\.masterPlaylist\s*=\s*(.*?)\s*window\.canPlayFHD', page, re.IGNORECASE)
        if match:
            jj = match.group(1).strip()
            ff = jj[:-3] + "}"
            ff = ff.replace("'", '"')
            ff = ff.replace("url", '"url"')
            ff = ff.replace("params", '"params"')
            ff = re.sub(r',\s*}', '}', ff)
            logga("TMDB_FF: "+ff)
            arr_t = json.loads(ff)
            token = arr_t["params"]["token"]
            expires = arr_t["params"]["expires"]
            url_v = arr_t["url"]
            
            to_ret = f"{url_v}?token={token}&expires={expires}&h=1"
        else:
            logga("NO TMDB_JSON")
    except Exception as e:
        logga(f"Error: {e}")
    
    video_urls = []
    jsonText='{"SetViewMode":"50","items":['
    jsonText = jsonText + '{"title":"[COLOR lime]PLAY STREAM (IT)[/COLOR]","link":"'+to_ret+'&lang=it",'
    jsonText = jsonText + '"thumbnail":"https://cdn3d.iconscout.com/3d/premium/thumb/watching-movie-4843361-4060927.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"},'
    jsonText = jsonText + '{"title":"[COLOR lime]PLAY STREAM (EN)[/COLOR]","link":"'+to_ret+'&lang=en",'
    jsonText = jsonText + '"thumbnail":"https://cdn3d.iconscout.com/3d/premium/thumb/watching-movie-4843361-4060927.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"}'
    
    
    jsonText = jsonText + "]}"
    logga('JSON-TMDB: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    
    return video_urls

def get_tmdb_episode_video(tmdb_id="1416_1_1"):
    import json
    to_ret = "ignoreMe"
    arrV=tmdb_id.split("_")
    serieId=arrV[0]
    season=arrV[1]
    episode=arrV[2]
    url = "https://vixsrc.to/tv/{serieId}/{season}/{episode}?lang=it"
    
    try:
        response = requests.get(url)
        page = response.text.replace("\n", "").replace("\r", "").replace("\t", "")
        
        match = re.search(r'window\.masterPlaylist\s*=\s*(.*?)\s*window\.canPlayFHD', page, re.IGNORECASE)
        if match:
            jj = match.group(1).strip()
            ff = jj[:-3] + "}"
            ff = ff.replace("'", '"')
            ff = ff.replace("url", '"url"')
            ff = ff.replace("params", '"params"')
            ff = re.sub(r',\s*}', '}', ff)
            
            arr_t = json.loads(ff)
            token = arr_t["params"]["token"]
            expires = arr_t["params"]["expires"]
            url_v = arr_t["url"]
            
            to_ret = f"{url_v}?token={token}&expires={expires}&h=1&lang=it"
    except Exception as e:
        print(f"Error: {e}")
    
    video_urls = []
    jsonText='{"SetViewMode":"50","items":['
    jsonText = jsonText + '{"title":"[COLOR lime]PLAY STREAM[/COLOR]","link":"'+to_ret+'",'
    jsonText = jsonText + '"thumbnail":"https://cdn3d.iconscout.com/3d/premium/thumb/watching-movie-4843361-4060927.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"URL: '+to_ret+'"}'
    
    
    jsonText = jsonText + "]}"
    logga('JSON-TMDB: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    
    return video_urls


def sibNet(parIn=None):
    video_urls = []
    
    #randomUa=getRandomUA()
    randomUa="iPad"
    urlP="https://video.sibnet.ru/shell.php?videoid="+parIn
    dataJson = requests.get(urlP,headers={'user-agent':randomUa,'accept':'*/*','Referer':'https://video.sibnet.ru/','Origin':'https://video.sibnet.ru'}).content
    
    if PY3:
        dataJson = dataJson.decode('Latin-1')
    
    logga('SIBNET_CONTENT: '+dataJson)
    tito = preg_match(dataJson, "title: '(.*?)',")
    if tito != None:
        tito= tito.replace("[B]","").replace("[/B]","").replace("[/COLOR]","")
        tito= tito.replace("[COLOR lime]","").replace("[COLOR aqua]","").replace("[COLOR gold]","")
        tito= tito.replace("[COLOR white]","").replace("[COLOR red]","").replace("[COLOR blue]","")
        tito = "[COLOR lime]"+tito+"[/COLOR]"
    else:
        tito = "[COLOR orange]PLAY STREAM[/COLOR]"
    iframe_url = preg_match(dataJson, 'player.src\(\[\{src: "(.*?)", type')
    logga('URL SIB: '+iframe_url)
    if iframe_url != None:
        iframe_url ="https://video.sibnet.ru"+iframe_url
    else:
        iframe_url = "https://static.videezy.com/system/resources/previews/000/039/863/original/Movie-countdown-2.mp4"
        tito = "[COLOR red]NO LINK FOUND[/COLOR]"
    video_urls.append((iframe_url+"|Referer=https://video.sibnet.ru/&Origin=https://video.sibnet.ru&User-Agent=iPad", tito , "PLAY VIDEO ", "https://clipart-library.com/image_gallery2/Television-Free-Download-PNG.png"))
    return video_urls

def freeshot(codeIn=None):
    video_urls = []
    randomUa="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0"
    #randomUa=getRandomUA()
    headers = {
        'user-agent': randomUa,
        'referer': "https://thisnot.business/"
    }
    s = requests.Session()
    #urlAuth="https://popcdn.day/go.php?stream="+codeIn
    urlAuth="https://popcdn.day/player/"+codeIn
    fu = s.get(urlAuth, headers=headers)
    #logga("FREE_PAGE: "+fu.text)

    '''
    frameUrl = preg_match(fu.text, 'frameborder="0" src="(.*?)"')
    arrTk=frameUrl.split("token=")
    tk1=arrTk[1]
    arrTk2=tk1.split("&")
    token=arrTk2[0]
    '''
    token = preg_match(fu.text, 'currentToken: "(.*?)"')
    #logga ("TOKEN: "+token)
    
    link_ch="https://planetary.lovecdn.ru/"+codeIn+"/tracks-v1a1/mono.m3u8?token="+token
    #link_ch=frameUrl.replace("embed.html", "index.fmp4.m3u8")
    jsonText='{"SetViewMode":"50","items":['
    jsonText = jsonText + '{"title":"[COLOR orange]PLAY STREAM [/COLOR] [COLOR gold](FFMPEG)[/COLOR]","myresolve":"ffmpeg_noRef@@'+link_ch+'",'
    jsonText = jsonText + '"thumbnail":"https://i.imgur.com/8EL6mr3.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"},'
    jsonText = jsonText + '{"title":"[COLOR lime]PLAY STREAM [/COLOR] [COLOR gold](PLAYER EST.)[/COLOR]","link":"'+link_ch+'",'
    jsonText = jsonText + '"thumbnail":"https://i.imgur.com/8EL6mr3.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"}'
    
    
   
    
    jsonText = jsonText + "]}"
    logga('JSON-FREE: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    
    return video_urls

def tvapp(parIn=None):
    import json
    video_urls = []
    randomUa="Mozilla/5.0"
    #randomUa=getRandomUA()
    headers = {
        'user-agent': randomUa,
        'referer': "https://thetvapp.to/"
    }
    s = requests.Session()
    urlAuth="https://thetvapp.to/tv/"+parIn
    fu = s.get(urlAuth, headers=headers)
    divUrl = preg_match(fu.text, '<div id="stream_name" name="(.*?)">')
    urlJsonLink="https://thetvapp.to/token/"+divUrl
    fuJson = s.get(urlJsonLink, headers=headers).text
    logga("JSON TVAPP: "+fuJson)
    arrJ = json.loads(fuJson)
    videoLink=arrJ["url"]
    logga("LINK TVAPP: "+videoLink)
    
    video_urls.append((videoLink, "[COLOR lime]PLAY STREAM (PLAYER EST.)[/COLOR]", "PLAY STREAM", "https://www.pepperlive.info/Live1.jpg"))
    return video_urls


def enigma4k(parIn=None):
    import json
    
    randomUa=getRandomUA()
    urlP="https://enigma4k.live/get_video_link.php?id="+parIn
    dataJson = requests.get(urlP,headers={'user-agent':randomUa,'accept':'*/*','Referer':'https://enigma4k.live'}).content
    if PY3:
        dataJson = dataJson.decode('utf-8')
    logga("JSON ENIGMA: "+dataJson)
    arrJ = json.loads(dataJson)
    videoLink=arrJ["videoLink"]
    logga("LINK ENIGMA: "+videoLink)
    return urlsolver(videoLink)

def pepper(parIn=None):
    video_urls = []
    randomUa=getRandomUA()
    page_data = requests.get(parIn,headers={'user-agent':randomUa,'accept':'*/*','Referer':'https://www.pepperlive.info'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    iframe_url = preg_match(page_data, '<iframe width="100%" height="100%" allow=\'encrypted-media\' src="(.*?)"')
    logga('URL PEPPER: https:'+iframe_url)
    if "amstaff.city" in iframe_url:
        iframe_url2=iframe_url
        return nopay("https:"+iframe_url2)
    if "embed" in iframe_url:
        iframe_url2=iframe_url
        video_url=checkUnpacked("https:"+iframe_url2)
    else:
        page_data2 = requests.get("https:"+iframe_url,headers={'user-agent':randomUa,'accept':'*/*','Referer':parIn}).content
        if PY3:
            try:
                page_data2 = page_data2.decode('utf-8')
            except:
                page_data2 = page_data2.decode('latin1')
        iframe_url2 = preg_match(page_data2, '<iframe src="(.*?)"')
        logga('URL PEPPER2: https:'+iframe_url2)
        video_url = GetLSProData("https:"+iframe_url2, parIn)
    final_url = video_url + "|connection=keepalive&Referer=https:"+iframe_url2+"&User-Agent="+randomUa
    video_urls.append((final_url, "[COLOR lime]PLAY STREAM[/COLOR]", "PLAY: "+video_url, "https://www.pepperlive.info/Live1.jpg"))
    return video_urls

def wikisport(parIn=None):
    video_urls = []
    randomUa = getRandomUA()
    pageUrl = "https://fiveyardlab.com/wiki.php?player=desktop&live="+parIn
    page_data = requests.get(pageUrl,headers={'user-agent':randomUa,'accept':'*/*','Referer':'https://wikisport.click'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    #logga('wikisport page: '+pageUrl+"\n"+page_data)
    iframe_url = preg_match(page_data, 'return\(\[(.*?)\]')
    final_url = iframe_url.replace('"', '').replace(",", "").replace("\\", "").replace("https:////", "https://")
    logga('URL wikisport: '+final_url)
    video_urls.append((final_url+ "|connection=keepalive&Referer="+pageUrl+"&Origin=https://wikisport.click&User-Agent="+randomUa, "[COLOR lime]PLAY STREAM[/COLOR]", "PLAY: ", "https://www.pepperlive.info/Live1.jpg"))
    return video_urls

def daily(parIn=None):
    import json
    video_urls = []
    randomUa=getRandomUA()
    urlAny="https://www.dailymotion.com/player/metadata/video/"+parIn
    data = requests.get(urlAny,headers={'user-agent':randomUa,'accept':'*/*','Referer':'https://www.dailymotion.com'}).content
    if PY3:
        data = data.decode('utf-8')
    logga('JSON DAILY: '+data)
    dataJ = json.loads(data)
    name=dataJ["title"]
    url=dataJ["qualities"]["auto"][0]["url"]
    img="https://png.pngtree.com/png-vector/20230124/ourmid/pngtree-arrow-icon-3d-play-png-image_6565151.png"
    try:
        img=dataJ["posters"]["720"]
    except:
        pass
    video_urls.append((url, "[COLOR lime]"+name+"[/COLOR]", "by MandraKodi", img))
    return video_urls


def anyplay(parIn=None):
    import json
    logoCh="https://png.pngtree.com/png-vector/20230124/ourmid/pngtree-arrow-icon-3d-play-png-image_6565151.png"
    video_urls = []
    randomUa=getRandomUA()
    urlAny="https://aniplay.co/series/"+parIn
    page_data = requests.get(urlAny,headers={'user-agent':randomUa,'accept':'*/*','Referer':'https://aniplay.co/'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    dataJ = preg_match(page_data, 'const data = \[(.*?)\];')
    #logga('ANY JSON'+dataJ)
    arrP1 = dataJ.split(',episodes:')
    srrs = arrP1[1]
    arrP2 = srrs.split(',similarSeries:')
    dj2='{"episodes":'+arrP2[0]
    #logga("ANY PAGE ANTE\n"+dj2)
    mapping = {'old_id:':'"old_id":', 'id:':'"id":', 'subbed:':'"subbed":', 'download_link:':'"download_link":', 'title:':'"title":', 'slug:':'"slug":', 'number:':'"number":', 'score:':'"score":', 'user:':'"user":', 'username:':'"username":', 'email:':'"email":', 'provider:':'"provider":', 'password:':'"password":', 'resetPasswordToken:':'"resetPasswordToken":', 'confirmationToken:':'"confirmationToken":', 'confirmed:':'"confirmed":', 'blocked:':'"blocked":', 'avatar_url:':'"avatar_url":', 'gender:':'"gender":', 'banner_url:':'"banner_url":', 'bio:':'"bio":', 'settingsProfileVisibility:':'"settingsProfileVisibility":', 'title:':'"title":', 'temp_sub:':'"temp_sub":', 'quality:':'"quality":', 'release_date:':'"release_date":', 'seconds:null':'"seconds":"0"', 'streaming_link:':'"streaming_link":', 'birth_date:':'"birth_date":', 'seconds:':'"seconds":', 'embed:':'"embed":', 'createdAt:':'"createdAt":', 'updatedAt:':'"updatedAt":', 'publishedAt:':'"publishedAt":', 'settingsProfileComments:':'"settingsProfileComments":', 'home_visibile:':'"home_visibile":', 'location:':'"location":', 'release_hour:':'"release_hour":'}
    for k, v in mapping.items():
        dj2 = dj2.replace(k, v)

    #logga("ANY PAGE POST\n"+dj2)
    jsonText='{"SetViewMode":"503","items":['
    numIt=0
    arrJ = json.loads(dj2)
    for ep in arrJ["episodes"]:
        link=ep["streaming_link"]
        title=""
        if not ep["title"] is None: 
            title=ep["title"]
        numEp=str(ep["number"])
        if (int(numEp)<0):
            numEp="0"+numEp
        tit="Ep. "+numEp+" - "+title
        #logga(tit+" "+link) 
        if (numIt > 0):
            jsonText = jsonText + ','    
        jsonText = jsonText + '{"title":"[COLOR gold]'+tit+'[/COLOR]","link":"'+link+'",'
        jsonText = jsonText + '"thumbnail":"'+logoCh+'",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"by MandraKodi"}'
        numIt=numIt+1
    
    jsonText = jsonText + "]}"
    logga('JSON-ANY: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls

def getSourceFrame(parIn):
    import re
    from urllib.parse import quote_plus
    toRet="ignore"
    video_urls = []
    UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'
    referer = parIn
    headers = {
        'user-agent': UA
    }

    s = requests.Session()
    r = s.get(parIn, headers=headers)
    express = r"<iframe src='(.*?)'"
    try:
        srcIfra = re.compile(express, re.MULTILINE | re.DOTALL).findall(r.text)[0]
        logga("FIND IFRAME: "+srcIfra)
        headers = {
            "user-agent": UA,
            "referer": parIn
        }
        a = s.get(srcIfra, headers=headers)
        express = r"source:'(.*?)'"
        toRet = re.compile(express, re.MULTILINE | re.DOTALL).findall(a.text)[0]
    except:
        pass
    texto="[COLOR red]NO LINK FOUND[/COLOR]"
    if toRet != "ignore":
        from urllib.parse import urlparse
        parsed_uri = urlparse(srcIfra)
        result = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        referer = quote_plus(srcIfra)
        origin = quote_plus(parIn)
        user_agent = quote_plus(UA)
        toRet += "|Referer="+srcIfra+"&Origin="+result+"&Keep-Alive=true&User-Agent="+user_agent
        texto="[COLOR lime]PLAY[/COLOR]"
    video_urls.append((toRet, texto))
    return video_urls



def PlayStream(link):
    import re, json, base64
    logga("CH_DADDY: "+link)
    randomUa="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0"
    
    headers = {
        'user-agent': randomUa,
        'referer': "https://daddylivestream.com/"
    }
    s = requests.Session()
    
    urlAuth="https://dokoplay.xyz/premiumtv/daddylive.php?id="+link
    fu = s.get(urlAuth, headers=headers)
    logga ("AUTH_PAGE: "+fu.text)

    bundle64 = re.findall('const XJZ="(.*?)"', fu.text)[0]
    logga("BUNDLE_DADDY: "+bundle64)
    bundle=base64.b64decode(bundle64).decode("utf-8")
    arrAuth=json.loads(bundle)
    authTs64 = arrAuth["b_ts"]
    authRnd64 = arrAuth["b_rnd"]
    authSig64 = arrAuth["b_sig"]

    authTs = base64.b64decode(authTs64).decode("utf-8")
    authRnd = base64.b64decode(authRnd64).decode("utf-8")
    authSig = base64.b64decode(authSig64).decode("utf-8")
    


    headers = {
        'user-agent': randomUa,
        'referer': "https://dokoplay.xyz/",
        'origin': "https://dokoplay.xyz"
    }
    urlAuth="https://top2new.kiko2.ru/auth.php?channel_id=premium"+link+"&ts="+authTs+"&rnd="+authRnd+"&sig="+authSig
    dataJ2 = s.get(urlAuth, headers=headers)
    logga("DADDY AUTH "+urlAuth+"\n"+dataJ2.text)
    
    
    
    
    urlSrv="https://dokoplay.xyz/server_lookup.php?channel_id=premium"+link
    dataJson = s.get(urlSrv, headers=headers)
    arrJ = json.loads(dataJson.text)
    server=arrJ["server_key"]
    link="https://"+server+"new.kiko2.ru/"+server+"/premium"+link+"/mono.m3u8"
    refe="https://dokoplay.xyz/"
    origin="https://dokoplay.xyz"
    
    
    final_url=link+"|Referer="+refe+"&Origin="+origin+"&User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0"
    

    liz = xbmcgui.ListItem('Daddylive', path=final_url)
    liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
    liz.setMimeType('application/x-mpegURL')
    liz.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
    liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
    timeShift = xbmcaddon.Addon(id=addon_id).getSetting("urlAppo4")
    logga("TimeShift ==> "+timeShift)
    if timeShift != "no_time_shift":
        logga("OK TimeShift")
        liz.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
    
    return liz

def daznTokenOld(parIn):
    logga ("PAR_DAZN: "+parIn)
    arrT=parIn.split("SPLITTA_QUI")
    link=arrT[0].replace("PARAMETRI_TUOI", "&")
    key=arrT[1]
    token=arrT[2]
    ua=arrT[3]
    drmType="org.w3.clearkey"
    host="https://www.dazn.com"
    logga ("link_DAZN: "+link)

    liz = xbmcgui.ListItem(path=link, offscreen=True)
    liz.setContentLookup(False)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setMimeType("application/dash+xml")
    liz.setProperty('inputstream.adaptive.file_type', 'mpd')
    liz.setProperty('inputstream.adaptive.drm_legacy', drmType+'|'+key)
    heads="dazn-token="+token+'&referer='+host+'/&origin='+host+'&user-agent='+ua
    liz.setProperty('inputstream.adaptive.stream_headers', heads)
    liz.setProperty('inputstream.adaptive.manifest_headers', heads)

    return liz

def amstaffTest(parIn):
    import base64
    if "http" in parIn:
        logga("NO_BASE64")
        parametro=parIn
    else:
        parametro=base64.b64decode(fix_base64_padding(parIn)).decode("utf-8")
    
    win = xbmcgui.Window(10000)
    sessionVar1 = win.getProperty("sessionVar1")
    logga('sessionVar1: '+sessionVar1)
    arrT=parametro.split("|")
    link=arrT[0]
    key64=arrT[1]
    token=""
    try:
      token=arrT[2]
    except:
        pass
    drmType="org.w3.clearkey"
    
    liz = xbmcgui.ListItem(path=link, offscreen=True)
    liz.setContentLookup(False)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    if ".mpd" in link:
        liz.setMimeType("application/dash+xml")
        liz.setProperty('inputstream.adaptive.file_type', 'mpd')
    
    if ".m3u8" in link:
        liz.setMimeType("application/x-mpegURL")
        liz.setProperty('inputstream.adaptive.file_type', 'hls')
        #drmType="none"
    
    if key64!="0000":
        liz.setProperty('inputstream.adaptive.drm_legacy', drmType+'|'+key64)
    
    ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0"
    if "dazn" in link or "dai.google.com" in link:
        #ua="Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) QtWebEngine/5.9.7 Chrome/56.0.2924.122 Safari/537.36 Sky_STB_ST412_2018/1.0.0 (Sky, EM150UK,)"
        ua=myParse.quote("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36")
        host="https://www.dazn.com"
        heads='User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false'
        if token != "":
            ua=myParse.quote_plus("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
            heads=token+'&referer='+host+'/&origin='+host+'&user-agent='+ua
        liz.setProperty('inputstream.adaptive.stream_headers', heads)
        liz.setProperty('inputstream.adaptive.manifest_headers', heads)
    elif "lba-ew" in link:
        ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0"
        host="https://www.lbatv.com"
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
        liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
    elif "discovery" in link:
        ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"
        host="https://www.discoveryplus.com"
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
        liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
    elif "nowitlin" in link:
        ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        host="https://www.nowtv.it"
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
        liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
    elif "vodafone.pt" in link:
        ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"
        host="http://rr.cdn.vodafone.pt"
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
        liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
    elif "clarovideo.com" in link:
        ua=myParse.quote_plus("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0")
        host="https://clarovideo.com"
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
        liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
    elif "starzplayarabia" in link:
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&verifypeer=false')
        liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&verifypeer=false')
    else:
        arrF=link.split("/")
        host="https://"+arrF[2]
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
        liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false')
    if token != "":
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+ua+'&Referer='+host+'/&Origin='+host+'&verifypeer=false') 
    return liz

def daznToken(parIn):
    import base64
    drmType="org.w3.clearkey"
    parametro=base64.b64decode(fix_base64_padding(parIn)).decode("utf-8")
    arrTmp=parametro.split("|")
    link=arrTmp[0]
    key=arrTmp[1]
    token=arrTmp[2]
    ua=myParse.quote_plus("Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0")
    try:
        ua=arrTmp[3]
    except:
        pass
    
    liz = xbmcgui.ListItem(path=link, offscreen=True)
    liz.setContentLookup(False)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setProperty('inputstream.adaptive.drm_legacy', drmType+'|'+key)
    liz.setProperty('inputstream.adaptive.stream_headers', "dazn-token="+token+"&User-Agent="+ua)
    liz.setProperty('inputstream.adaptive.manifest_headers', "dazn-token="+token+"&User-Agent="+ua)
    
    return liz



def amstaff(parIn):
    import base64, urllib.parse
    headers = dict()
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    headers['Referer'] = "https://amstaff.city/"
    headers['Origin'] = "https://amstaff.city"
    parHead=urllib.parse.urlencode(headers)
    logga("AMSTAFF_HEAD: "+parHead)


    phd="Referer=https://amstaff.city/&Origin=https://amstaff.city&User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    arrT=parIn.split("|")
    link=arrT[0]
    key=arrT[1]
    b64_string = key
    #b64_string += "=" * ((4 - len(b64_string) % 4) % 4)
    key64=base64.b64decode(b64_string).decode("utf-8").replace("{","").replace("}","").replace('"',"")
    logga("AMSTAFF64: "+key64)
    liz = xbmcgui.ListItem('Amstaff', path=link)
    liz.setMimeType('application/dash+xml')
    liz.setContentLookup(False)
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setProperty('inputstream.adaptive.file_type', 'mpd')
    liz.setProperty('inputstream.adaptive.license_type', 'clearkey')
    liz.setProperty('inputstream.adaptive.license_key', key64)
    liz.setProperty('inputstream.adaptive.stream_headers', phd)
    liz.setProperty('inputstream.adaptive.manifest_headers', phd)
    return liz

   
def proData(parIn=None, flat=0):
    video_urls = []
    logga('PAR: '+parIn)
    if "supervideo.tv" in parIn or "supervideo.cc" in parIn:
        logga('CALL SUPERVIDEO')
        return supervideo(parIn)
    video_url = GetLSProData(parIn)
    logga('URL PRODATA: '+video_url)
    if "sportsonline.ps" in parIn:
        arrTT=video_url.split("|")
        ref=arrTT[1]
        vid=arrTT[0]
        video_url = vid + "|Referer=https://forgepattern.net&Origin=https://forgepattern.net&User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%3B+rv%3A98.0%29+Gecko%2F20100101+Firefox%2F98.0&Keep-Alive=true"
        #video_url += ref.replace("referer", "&Origin") + "&User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%3B+rv%3A98.0%29+Gecko%2F20100101+Firefox%2F98.0&Keep-Alive=true"
        logga('URL sportsonline: '+video_url)
    if flat==1:
        return video_url
    video_urls.append((video_url, "[COLOR lime]PLAY STREAM [/COLOR]", "by @MandraKodi"))
    video_urls.append((video_url+"&verifypeer=false", "[COLOR orange]PLAY STREAM 2 [/COLOR]", "by @MandraKodi"))
    return video_urls


def decodeProtected(linkIn):
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    page=s.get(linkIn, allow_redirects=False,timeout=20)
    redir=page.headers["Location"]
    logga("TROVATO: "+redir+" FROM "+page.url)
    return redir

def gaga(linkIn):
    video_urls = []
    url=checkUnpacked(linkIn, "https://calcio.events")
    logga ("URL_GAGA: "+url)
    video_urls.append((url, "[COLOR lime]PLAY STREAM GAGA[/COLOR]", "by @MandraKodi"))
    return video_urls

def checkUnpacked(page_in, refe=""):
    import jsunpack
    toRet=""
    myRefe=page_in
    if refe != "":
        myRefe=refe
    logga("checkUnpacked: "+page_in)
    fu = downloadHttpPage(page_in, headers={'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36','referer':myRefe})
    if fu != "":
        #logga("RESULT: "+fu)
        find = ""
        try:
            find = re.findall('eval\(function(.+?.+)', fu)[0]
            unpack = jsunpack.unpack(find)
            logga('UNPACK: '+unpack)
            try:
                toRet = re.findall('src:"([^"]*)',unpack)[0]
            except:
                try:
                    toRet = re.findall('file:"([^"]*)',unpack)[0]
                except:
                    try:
                        toRet = re.findall('src="([^"]*)',unpack)[0]
                    except:
                        try:
                            toRet = re.findall('source:"([^"]*)',unpack)[0]
                        except:
                            pass
            logga('URL_UNPACK '+toRet)
        except:
            pass
    else:
        logga('LA PAGINA '+page_in+' NON RISPONDE')
        toRet="NO_PAGE"
    toRet = 'https:' + toRet if toRet.startswith('//') else toRet
    return toRet

def GetLSProData(page_in, refe=None):
    import jsunpack, time

    logga('page_in '+page_in)
    if refe != None:
        logga('REFER '+refe)
    
    c = checkUnpacked(page_in)
    if c == "NO_PAGE":
        dialog = xbmcgui.Dialog()
        mess = 'La pagina '+page_in+' non risponde'
        dialog.ok("Mandrakodi", mess)
        return ""
    if c != "":
        logga('UNPACKED')
        return c

    if "streamhide.to" in page_in:
        logga('URL_STREAMHIDE ')
        return findM3u8(page_in, page_in)

    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    r = s.get(page_in, headers=headers) 

    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    time.sleep(2)
    s = requests.Session()
    page_data = s.get(page_in, headers=headers).content

    #page_data = requests.get(page_in,headers={'user-agent':'iPad','accept':'*/*','referer':refe}).content

    if PY3:
        try:
            page_data = page_data.decode('utf-8')
        except:
            page_data = page_data.decode('latin1')

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
    logga('GetLSProData_iframe_url '+src)

    if "nopay2.info" in page_in and src.startswith('/ch/'):
        logga('starlive.xyz ')
        pageNew="https://nopay2.info"+src
        fu = requests.get(pageNew, headers={'user-agent':'iPad','referer':page_in}).text
        find = re.findall("source: '(.*?)'", fu)[0]
        return find+"|referer=https://nopay.info"+src
    elif "enigma4k.live" in page_in:
        logga('enigma4k.live ')
        return GetLSProData(src, page_in)
    elif "buzztv" in src:
        logga('BUZZTV ')
        return GetLSProData(src)
    elif "embed" in src and ("tutele1" in page_in or "starlive" in page_in or "elixx" in page_in or "sportsonline" in page_in or "pepperlive" in page_in or "l1l1.to" in page_in or "buzztv" in page_in):
        logga('iframe_embed for '+page_in)
    elif "starlive.xyz" in src:
        logga('starlive.xyz ')
        return GetLSProData(src)
    elif "protectlink.stream" in src:
        logga('protectlink.stream')
        newSrc=decodeProtected(src)
        return resolveMyUrl(newSrc)
    elif "cloudstream" in src:
        logga('CLOUDSTREAM')
        return GetLSProData(src)
    elif "supervideo.tv" in src:
        logga('SUPERVIDEO')
        return supervideo(src)
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
        logga('EVAL ==> '+find)
        unpack = jsunpack.unpack(find)
        logga('UNPACK ==> '+unpack)
        c = re.findall('var src="([^"]*)',unpack)[0]
        return c + '|referer=' + src
    except:
        return page_in

def sportOnline(parIn=None):
    logga('PAR_SPONL: '+parIn)
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    fu = s.get(parIn, headers=headers)
    find = re.findall('<iframe src="(.*?)"', fu.text)[0]
    if (find[0:1]=="/"):
        find="https:"+find
    logga('IFRAME_SPONL: '+find)
    return wigi(find+"|https://sportsonline.si/")


def wigi(parIn=None):
    import jsunpack
    logga('PAR_WIGI: '+parIn)
    if "amstaff.city" in parIn or "nopay2.info" in parIn:
        return nopay(parIn.replace("nopay.info", "nopay2.info"))
    
    video_urls = []

    refe = ""
    wigiUrl = ""
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    if "|" in parIn:
        arr=parIn.split("|")
        wigiUrl = arr[0]
        refe = arr[1]
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
            "Referer": refe
        }
    else:
       wigiUrl = parIn
       refe = parIn 
        
    logga('URL_WIGI: '+wigiUrl)
    logga('URL_REFE: '+refe)

    s = requests.Session()
    fu = s.get(wigiUrl, headers=headers)
    video_url = wigiUrl
    try:
        find = re.findall('eval\(function(.+?.+)', fu.text)[1]
        unpack = jsunpack.unpack(find)
        c = re.findall('var src="([^"]*)',unpack)[0]
        video_url = c + '|referer=' + wigiUrl
    except:
        logga("NO PACKED \n"+fu.text)
        pass


    logga('video_url '+video_url)
    msg = "[COLOR lime]PLAY STREAM[/COLOR]"
    if video_url == '' or video_url == wigiUrl:
        msg = "NO LINK FOUND"
    video_urls.append((video_url+"&connection=keepalive", msg))
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
            video_urls.append((resolvedUrl, "[COLOR gold]LINK 1[/COLOR]"))
            if "|" in resolvedUrl:
                video_urls.append((resolvedUrl+"&verifypeer=false", "[COLOR lime]LINK 2[/COLOR]"))
                arrV = resolvedUrl.split("|")
                linkClean=arrV[0]
                logga('video_resolved_cleaned '+linkClean)
                video_urls.append((linkClean, "[COLOR orange]LINK 3[/COLOR]"))		
            else:
                randomUa=getRandomUA()
                final_url = resolvedUrl + "|verifyPeer=false&connection=keepalive&Referer="+url+"&User-Agent="+randomUa
                video_urls.append((final_url, "[COLOR lime]LINK 2[/COLOR]"))
            return video_urls
    
    return url

def uprot(parIn):
    video_urls = []
    logga("UPROT URL IN: "+parIn)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
        "Referer": "https://toonita.green/"
    }
    s = requests.Session()
    fu = s.get(parIn, headers=headers)
    logga("UPROT TEXT: "+fu.text)
    video_url = parIn
    try:
        fu2=fu.text.replace("\n", "").replace("\r", "").replace("\t", "")
        find = preg_match(fu2, r'<div id="ad_space">\s*<center><a href="(.*?)"><button')
        #logga("HTML\n"+fu2+"\n"+find)
        if "maxstream.video" in find:
            fu = s.get(find, headers=headers)
            fu3=fu.text.replace("\n", "").replace("\r", "").replace("\t", "")
            find2 = preg_match(fu3, r'src="https://maxstream.video/(.*?)" scrolling="no">')
            #logga("UPROT URL maxstream: "+find2+"\n"+fu3)
            if find2!="":
                find=find2
        return resolveMyUrl(find)
    except:
        logga("NO link \n"+fu2)
        video_urls.append(("ignore", "[COLOR red]NO LINK FOUND[/COLOR]"))	
        pass
    return video_urls

def toonIta(parIn):
    logga("TOONITA URL IN: "+parIn)
    video_urls = []
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
        "Referer": "https://toonita.green/"
    }
    s = requests.Session()
    fu = s.get(parIn, headers=headers)
    video_url = parIn
    try:
        pageHtml=fu.text
        logga("TOONITA HTML: "+pageHtml)
        listaHtml=pageHtml.split("</td>")
        numero=len(listaHtml)
        logga("TOONITA TR: "+str(numero))
        my_list = []
        for (row) in listaHtml:
            logga("TOONITA ROW: "+row)
            regEx= r'href="https:\/\/uprot.net\/(.*?)\/(.*?)" target="_blank" rel="noopener nofollow" title="(.*?)"'
            list=preg_match(row, regEx)
            #list = re.compile(regEx, re.MULTILINE | re.DOTALL).findall(row)
            for (host, id, title) in list:
                ep=title.replace("Streaming di ", "").replace(" su StreamTape", "").replace(" su Max", "").replace(" su Flexy", "")
                my_list.append(ep+"@@"+host+"@@"+id)


        #list = re.findall(regEx, fu.text)
        numero=len(my_list)
        logga("TOONITA TROVATI: "+str(numero))
        jsonText='{"SetViewMode":"51","channels":['
        numIt = 0
        numCh = -1
        oldEp = ""
        for (elem) in my_list:
            arrEl=elem.split("@@")
            title=arrEl[0]
            host=arrEl[1]
            id=arrEl[2]
            ep=title.replace("Streaming di ", "").replace(" su StreamTape", "").replace(" su Max", "").replace(" su Flexy", "")
            #logga("EP_07:"+ep[:7])
            if ep[:7]=="Scarica":
                continue
            
            if oldEp != ep:
                numCh = numCh+1
                oldEp = ep
                numIt = 0
                if (numCh > 0):
                    jsonText = jsonText + ']},'
                jsonText = jsonText + '{"name":"[COLOR lime]'+ep+'[/COLOR]",'
                jsonText = jsonText + '"thumbnail":"https://pbs.twimg.com/profile_images/848686618466816000/8MaqE-n5_400x400.jpg",'
                jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
                jsonText = jsonText + '"SetViewMode":"51","items":['
            
            if (numIt > 0):
                jsonText = jsonText + ',' 
            #jsonText = jsonText + '{"title":"[COLOR gold]'+host+'[/COLOR]","myresolve":"uprot@@https://uprot.net/'+host+'/'+id+'",'
            jsonText = jsonText + '{"title":"[COLOR gold]'+host+'[/COLOR]","myresolve":"uprot@@https://uprot.net/'+host+'/'+id+'",'
            jsonText = jsonText + '"thumbnail":"https://pbs.twimg.com/profile_images/848686618466816000/8MaqE-n5_400x400.jpg",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"info":"by MandraKodi"}'
            numIt=numIt+1
        
        
        
        if numIt==0:
            jsonText = jsonText + '{"title":"[COLOR red]NO HOST FOUND[/COLOR]","link":"ignore",'
            jsonText = jsonText + '"thumbnail":"https://pbs.twimg.com/profile_images/848686618466816000/8MaqE-n5_400x400.jpg",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"info":"NO INFO"}'

        jsonText = jsonText + "]}]}"
        logga("TOONITA JSON: "+jsonText)
        video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    except Exception as err:
        import traceback
        errMsg="ERRORE MANDRAKODI: {0}".format(err)
        #logging.warning(errMsg+"\nPAR_ERR --> ")
        traceback.print_exc()
        dialog = xbmcgui.Dialog()
        dialog.ok("Mandrakodi", errMsg)
        logga("NO PACKED \n"+fu.text)
        video_urls.append(("ignore", "[COLOR red]NO LINK FOUND[/COLOR]"))	
        pass
    return video_urls

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
    logga ("TRY TO RESOLVE "+url)
    resolved = ""
    try:
        hmf = resolveurl.HostedMediaFile(url)
        if hmf:
            resolved = hmf.resolve()
    except:
        pass
    if resolved:
        return resolved
    else:
        dialog = xbmcgui.Dialog()
        mess = "Spiacenti, ResolveUrl non ha trovato il link su "+url
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
    sc_url="https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/data/cs_url.txt"
    scUrl=makeRequest(sc_url)
    base=scUrl.replace("\n", '')+"watch/"
    
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
    #writeFileLog("SCOMM_PAGE: "+urlComm+"\n\n"+page_data, "w+")
    #patron = r'<video-player response="(.*?)">'
    patron = r'<div id="app" data-page="(.*?)">'
    jsonVideo = preg_match(page_data, patron)
    dataJson=jsonVideo.replace('&quot;', '"')
    arrJ = json.loads(dataJson)
    nameEp=arrJ["props"]["episode"]["name"]
    numEp=arrJ["props"]["episode"]["number"]
    numSeason=arrJ["props"]["episode"]["season"]["number"]
    titleEp=str(numSeason)+"x"+str(numEp)+" - "+nameEp
    scws_id = arrJ["props"]["episode"]["scws_id"]
    logga("scws_id => "+str(scws_id))
    return getUrlSc(str(scws_id), titleEp)

def getUrlSc(scws_id, tit=None):
    logga('getUrlSc '+scws_id)
    from time import time
    from base64 import b64encode
    from hashlib import md5
    import json
    titolo="PLAY VIDEO"
    if tit != None:
        titolo=tit
    video_urls = []
    randomUA=getRandomUA()
    
    randomUA="PlusMediaPlayer/0.0.9"
    page_data = requests.get("http://test34344.herokuapp.com/getMyIp.php", headers={'user-agent':'Mozilla/5.0','accept':'*/*'}).content
    if PY3:
        page_data = page_data.decode('utf-8')
    logga('IP_community '+page_data)
    try:
        arrJ2 = json.loads(page_data)
        clientIp = arrJ2["client_ip"]
        logga("LOCAL IP: "+clientIp)
    except:
        logga("NO LOCAL IP")
    if clientIp:
        expires = int(time() + 172800)
        token = b64encode(md5('{}{} Yc8U6r8KjAKAepEA'.format(expires, clientIp).encode('utf-8')).digest()).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
        url = 'https://scws.work/master/{}?token={}&expires={}&canCast=1&b=1&n=1'.format(scws_id, token, expires)
        url4 = url
        #url4 = url + "|User-Agent="+randomUA
        video_urls.append((url4, "[COLOR lime]"+titolo+"[/COLOR]", "by @mandrakodi", "https://cdn3d.iconscout.com/3d/premium/thumb/watching-movie-4843361-4060927.png"))
    return video_urls

def scwsNew(parIn=None, parInp2=0):
    import json
    logga("SCWS: "+parIn)
    video_urls = []

    sc_url="https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/data/cs_url.txt"
    scUrl=makeRequest(sc_url)
    base=scUrl.replace("\n", '')+"it/iframe/"+parIn

    randomUA=getRandomUA()

    headSCt={'user-agent':randomUA}

    pageT = requests.get(base,headers=headSCt).content
    if PY3:
        pageT = pageT.decode('utf-8')
    pageT = pageT.replace("\n", "").replace("\r", "").replace("\t", "")
    #logga("SC_PAGE: "+pageT)
    patron = r'src="(.*?)"'
    m3u8Url = preg_match(pageT, patron)
    logga("URL_M3U8: "+m3u8Url)
    arrT=m3u8Url.split("?")
    arrPar=m3u8Url.split("&amp;")
    baseUrl=arrT[0]
    pageT2 = requests.get(m3u8Url.replace("&amp;", "&"),headers=headSCt).content
    if PY3:
        pageT2 = pageT2.decode('utf-8')
    pageT3=pageT2.replace("\n", "").replace("\r", "").replace("\t", "")
    logga("pageT2: "+pageT3)
    urlSc="ignore"
    tito="[COLOR lime]PLAY VIDEO SC[/COLOR]"
    try:    
        patron = r"window.masterPlaylist\s=\s{\s.*params:\s(.*?)},\s.*url:\s'(.*?)'"
        res = preg_match(pageT3, patron)
        jsonUrl = ""
        jsonUrl = res[0]+'"url":"'+res[1]+'"}'
            
        #jsonUrl = preg_match(pageT3, patron)+'"sex":"ok"}'
        logga("JSON_M3U8: "+jsonUrl.replace("'", '"'))
        arrJ2 = json.loads(jsonUrl.replace("'", '"'))
        urlSc=baseUrl.replace("embed", "playlist")+"?token="+arrJ2["token"]+"&expires="+arrJ2["expires"]+"&n=1"
        urlTmp=arrJ2["url"]
        if "?" in urlTmp:
            urlSc=urlTmp+"&token="+arrJ2["token"]+"&expires="+arrJ2["expires"]+"&n=1"
        else:
           urlSc=urlTmp+"?token="+arrJ2["token"]+"&expires="+arrJ2["expires"]+"&n=1" 
        newPar=""
        numPar=0
        for param in arrPar:
            if numPar > 0:
                arrP2=param.split("=")
                if (arrP2[0]=="canPlayFHD"):
                    urlSc= urlSc + "&h=1"
                if (arrP2[0]=="b"):
                    urlSc= urlSc + "&b=1"
                #newPar = newPar+"&"+param
            numPar=numPar+1
        #urlSc= urlSc + newPar
        logga("FINAL URL: "+urlSc)
    except:
        tito="[COLOR red]NO VIDEO FOUND[/COLOR]"
    newUrl=urlSc+"|referer="+scUrl.replace("\n", '')+"&user-agent=Mozilla"
    video_urls.append((newUrl, tito, "by @mandrakodi", "https://cdn3d.iconscout.com/3d/premium/thumb/watching-movie-4843361-4060927.png"))
    
    if parInp2==1:
        liz = xbmcgui.ListItem('MovieUnity', path=newUrl)
        liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
        liz.setMimeType('application/x-mpegURL')
        liz.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
        liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
        timeShift = xbmcaddon.Addon(id=addon_id).getSetting("urlAppo4")
        if timeShift != "no_time_shift":
            liz.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
        
        return liz
    
    return video_urls


def scws(parIn=None):
    import json
    
    
    sc_url="https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/data/cs_url.txt"
    scUrl=makeRequest(sc_url)
    base=scUrl.replace("\n", '')+"it/titles/"+parIn
    randomUA=getRandomUA()

    headSCt={'user-agent':randomUA}
    pageT = requests.get(base,headers=headSCt).content
    if PY3:
        pageT = pageT.decode('utf-8')
    patron = r'<div id="app" data-page="(.*?)"'
    jsonCode = preg_match(pageT, patron)
    scwsId = 0
    titolo="NOT FOUND";
    try:
        arrJ2 = json.loads(jsonCode.replace("&quot;", '"'))
        scwsId = arrJ2["props"]["title"]["scws_id"]
        titolo = arrJ2["props"]["title"]["name"]
    except:
        logga("NO SCWS_ID FROM "+base)
    return getUrlSc(scwsId, titolo)

def getScSerie(parIn=None):
    import json
    logga("PAR_IN "+parIn)
    video_urls = []
    jsonText=""
    x = parIn.split("---")
    idSea=x[0]
    numSea=x[1]
    sc_url="https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/data/cs_url.txt"
    scUrl=makeRequest(sc_url)
    base=scUrl.replace("\n", '')+"it/titles/"+idSea+"/season-"+numSea
    randomUA=getRandomUA()

    headSCt={'user-agent':randomUA}
    pageT = requests.get(base,headers=headSCt).content
    if PY3:
        pageT = pageT.decode('utf-8')
    patron = r'<div id="app" data-page="(.*?)"'
    jsonCode = preg_match(pageT, patron)
    scwsId = 0
    titolo="NOT FOUND";
    logga ("JSON_CODE: "+jsonCode)
    try:
        arrJ2 = json.loads(jsonCode.replace("&quot;", '"'))
        
        titolo = arrJ2["props"]["title"]["name"]
        logga("titolo: "+titolo)
        img=""
        jsonText='{"SetViewMode":"503","items":['
        numIt=0
        for (immagine) in arrJ2["props"]["title"]["images"]:
            if (immagine["type"]=="cover"):
                img="https://cdn."+scUrl.replace("\n", '').replace("https://", '')+"images/"+immagine["filename"]
                logga("img: "+img)
        for (episodio) in arrJ2["props"]["loadedSeason"]["episodes"]:
            scwsId = str(episodio["scws_id"])
            urlIframe=idSea+"?episode_id="+str(episodio["id"])
            logga("urlIframe: "+urlIframe)
            numEp=str(episodio["number"])
            if (len(numEp)==1):
                numEp="0"+numEp
            logga("numEp: "+numEp)
            plot = "by MandraKodi"
            try:
                plot = episodio["plot"].replace("&#39;", "'").replace("&amp;", "&").replace("\n", " ").replace("\r", " ")
            except:
                pass    
            
            try:
                imgEp="https://cdn."+scUrl.replace("\n", '').replace("https://", '')+"images/"+episodio["images"][0]["filename"]
            except:
                imgEp=img
            
            eps="Episodio "+numEp
            try:
                eps=episodio["name"].replace("&#39;", "'").replace("&amp;", "&")
            except:
                pass

            
            try:
                titolo=numSea+"x"+numEp+" - "+eps
            
                newJson = '{"title":"[COLOR lime]'+titolo+'[/COLOR]","myresolve":"scws2@@'+urlIframe+'",'
                newJson += '"thumbnail":"'+imgEp+'",'
                newJson += '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
                newJson += '"info":"'+plot.replace('"','\\"')+'"}'
                json.loads(newJson)
                if (numIt > 0):
                    jsonText += ','
                jsonText +=  newJson
                numIt += 1
            except:
                logga("BAD ITEMS: "+newJson)
                pass
    except Exception as err:
        import traceback
        
        errMsg="ERROR_MK2: {0}".format(err)
        par=re.split('%3f', sys.argv[2])
        parErr = par[-1]
        logging.warning(errMsg+"\nPAR_ERR --> "+parErr)
        traceback.print_exc()

        logga("NO SCWS_ID FROM "+base)
        jsonText = jsonText + '{"title":"[COLOR red]NO PAGE FOUND[/COLOR]","link":"ignore",'
        jsonText = jsonText + '"thumbnail":"https://cdn-icons-png.flaticon.com/512/2748/2748558.png",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"NO PAGE FOUND"}'

    jsonText = jsonText + "]}"
    #logga('JSON-SC: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls


def pulive(parIn=None):
    url = "https://pulivetv146.com/player.html?id="+parIn
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

def m3uPlus(parIn=None):
    import json
    
    headers = {
        'user-agent':"ipad"
    }
    s = requests.Session()
        
    win = xbmcgui.Window(10000)
    
    arrIn=parIn.split("_@|@_")
    mode=arrIn[0]
    logga("M3UPLUS_MODE: "+mode)
    jsonText = ""
    if mode=="0":
        win.setProperty("sessionVar1", parIn)
        host=arrIn[1]
        usr=arrIn[2]
        pwd=arrIn[3]
        apiUrl="http://"+host+"/player_api.php?username="+usr+"&password="+pwd+"&action=get_live_categories"
        response = s.get(apiUrl, headers=headers)
        #logga("M3UPLUS_JSON: "+response.text)
        
        jsonText='{"SetViewMode":"503","items":['
        
        numIt=0
        lista = response.json()
        for item in lista:
            catId = item.get("category_id")
            name = item.get("category_name")
            if (numIt > 0):
                jsonText += ','
            numIt += 1
            
            jsonText = jsonText + '{"title":"[COLOR orange]=*= '+name+' =*=[/COLOR]","myresolve":"m3uPlus@@1_@|@_'+name+'_@|@_'+catId+'",'
            jsonText = jsonText + '"thumbnail":"https://static.vecteezy.com/system/resources/thumbnails/065/914/783/small/stylized-3d-rendering-of-a-file-folder-icon-for-data-management-free-png.png",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"info":"by MandraKodi"}'
            
        jsonText = jsonText + "]}"

    if mode=="1":
        parSess=win.getProperty("sessionVar1")
        catId=arrIn[2]
        arrSess=parSess.split("_@|@_")
        host=arrSess[1]
        usr=arrSess[2]
        pwd=arrSess[3]
        apiUrl="http://"+host+"/player_api.php?username="+usr+"&password="+pwd+"&action=get_live_streams&category_id="+catId
        response = s.get(apiUrl, headers=headers)

        jsonText='{"SetViewMode":"503","items":['
        
        numIt=0
        lista = response.json()
        for item in lista:
            stream_id = item.get("stream_id")
            linkUrl="http://"+host+"/live/"+usr+"/"+pwd+"/"+str(stream_id)+".ts"
            name = item.get("name")
            stream_icon = item.get("stream_icon")
            if (numIt > 0):
                jsonText += ','
            numIt += 1
            
            jsonText = jsonText + '{"title":"[COLOR lime]'+name+'[/COLOR]","link":"'+linkUrl+'|!User-Agent=VLC/3.0.9 LibVLC/3.0.9",'
            jsonText = jsonText + '"thumbnail":"'+stream_icon+'",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"info":"by MandraKodi"}'
            
        jsonText = jsonText + "]}"


    video_urls = []
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
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
    randomUa=getRandomUA()
    head={'user-agent':randomUa,'Content-Type':'application/x-www-form-urlencoded','Referer':'https://toonitalia.green/'}
    page_data = requests.get(ppIn, headers=head).content
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

def imdbList(parIn):
    import re
    video_urls = []
    page=1
    info = "NO - TIT"
    jsonText='{"SetViewMode":"503","items":['
    numIt=0
    while page < 6:
        urlPage="https://www.imdb.com/list/"+parIn+"/?page="+str(page)
        headers = {
            'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
        }

        s = requests.Session()
        r = s.get(urlPage, headers=headers)
        htmlFlat=r.text.replace("\n", '').replace("\r", '').replace("\t", '')
        
        if page==1:
            info = preg_match(htmlFlat, '<title>(.*?)</title>')
        
        express1 = r'<img alt="(.*?)"class="loadlate"loadlate="(.*?)"data-tconst="(.*?)"height="209"(.*?)<span class="lister-item-year text-muted unbold">(.*?)</span>'
        lista = re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)
        
        for (titolo, img, idImdb, par4, year) in lista:
            if (numIt > 0):
                jsonText = jsonText + ','    
            jsonText = jsonText + '{"title":"[COLOR gold]'+titolo+' '+year+'[/COLOR]","myresolve":"imdb@@'+idImdb+'",'
            jsonText = jsonText + '"thumbnail":"'+img+'",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"info":"'+idImdb+' - '+info.replace(" - IMDB", '')+'"}'
            numIt=numIt+1
        
        intEnd=1
        intMax=1
        try:
            (start, end, max) = preg_match(htmlFlat, '<span class="pagination-range">(.*?) - (.*?) of (.*?)</span>')
            logga('NUM REC: '+max)
            intEnd=int(end)
            intMax=int(max)
        except:
            pass
        nump = 1
        if intMax > intEnd:
            page = page + 1
        else:
            page = 6

    jsonText = jsonText + "]}"
    
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls

def webcam(parIn):
    import re
    video_urls = []
    arrT=parIn.split('_')
    mode=arrT[0]
    page=parIn[2:]
    urlPage="https://www.skylinewebcams.com/it/"+page+".html";
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }

    s = requests.Session()
    r = s.get(urlPage, headers=headers)
    htmlFlat=r.text.replace("\n", '').replace("\r", '').replace("\t", '')
    logga("FIND CAM ON "+urlPage)
    if mode == "0":
        express1 = r'<a href="it/webcam/(.*?)" class="col-xs-12 col-sm-6 col-md-4">(.*?)</a>'
        lista = re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)
        jsonText='{"SetViewMode":"503","items":['
        
        listaCam = []

        for (link, tit) in lista:
            titolo="Cam"
            express1 = r'<p class="tcam">(.*?)</p>'
            try:
                titolo = re.compile(express1, re.MULTILINE | re.DOTALL).findall(tit)[0]
            except:
                pass
            
            img="https://image.winudf.com/v2/image1/Y29tLm1pY3pvbi5hbmRyb2lkLndlYmNhbWFwcGxpY2F0aW9uX2ljb25fMTU3MjUxMTU1M18wNDU/icon.png?w=512&fakeurl=1"
            express1 = r'<img src="(.*?)"'
            try:
                img = re.compile(express1, re.MULTILINE | re.DOTALL).findall(tit)[0]
            except:
                pass
            
            info="by MandraKodi"
            express1 = r'<p class="subt">(.*?)</p>'
            try:
                info = re.compile(express1, re.MULTILINE | re.DOTALL).findall(tit)[0]
            except:
                pass
            
            infoPlus=""
            express1 = r'<span class="lcam">(.*?)</span>'
            try:
                infoPlus = re.compile(express1, re.MULTILINE | re.DOTALL).findall(tit)[0]
            except:
                pass
            
            strCam=titolo+"@@"+img+"@@"+link+"@@"+info+"@@"+infoPlus
            listaCam.append(strCam)

        listaCam.sort()
        numIt=0
        for wCam in listaCam:
            arrWcam=wCam.split("@@")
            titolo=arrWcam[0]
            img=arrWcam[1]
            link=arrWcam[2]
            info=arrWcam[3]
            infoPlus=arrWcam[4]
            infoP=""
            if infoPlus!="":
                infoP=" [COLOR lime]("+infoPlus+")[/COLOR]"
            if (numIt > 0):
                jsonText = jsonText + ','    
            jsonText = jsonText + '{"title":"[COLOR gold]'+titolo+'[/COLOR]'+infoP+'","myresolve":"webcam@@1_webcam/'+link.replace(".html", '')+'",'
            jsonText = jsonText + '"thumbnail":"'+img+'",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"info":"'+info+'"}'
            numIt=numIt+1
    
    if mode == "1":
        titolo="Watch Stream"
        info="by @mandrakodi"
        infoPlus=""
        img="https://image.winudf.com/v2/image1/Y29tLm1pY3pvbi5hbmRyb2lkLndlYmNhbWFwcGxpY2F0aW9uX2ljb25fMTU3MjUxMTU1M18wNDU/icon.png?w=512&fakeurl=1"

        express1 = r'<h1>(.*?)</h1>'
        try:
            titolo = re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)[0].replace("Live webcam", "")
        except:
            pass

        express1 = r'<h2>(.*?)</h2>'
        try:
            info = re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)[0]
        except:
            pass

        express1 = r'<meta property="og:description" content="(.*?)"'
        try:
            infoPlus = " "+re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)[0]
        except:
            pass

        express1 = r'<meta property="og:image" content="(.*?)"'
        try:
            img = re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)[0]
        except:
            pass
        tube=0
        url1="ignore"
        express1 = r"source:'(.*?)'"
        try:
            url = re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)[0]
            url1 = "https://hd-auth.skylinewebcams.com/"+url.replace("livee", 'live')+"|Referer="+urlPage+"&User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F109.0.0.0+Safari%2F537.36"
        except:
            pass

        if url1=="ignore":
            express1 = r"videoId:'(.*?)'"
            try:
                url = re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)[0]
                url1 = "https://www.youtube.com/watch?v="+url
                tube=1
            except:
                pass





        jsonText='{"SetViewMode":"503","items":['
        jsonText = jsonText + '{"title":"[COLOR gold]'+titolo+'[/COLOR]",'
        if tube==0:
            jsonText = jsonText + '"link":"'+url1+'",'
        else:
            jsonText = jsonText + '"myresolve":"risolvi@@'+url1+'",'
        jsonText = jsonText + '"thumbnail":"'+img+'",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"'+info+infoPlus+'"}'
        

    jsonText = jsonText + "]}"
    logga('JSON-WEBCAM: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls
    

def cb01(parIn):
    import re
    
    url="https://cb01.red/stream/"+parIn+"-movie.html";
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }

    s = requests.Session()
    r = s.get(url, headers=headers)
    logga("FIND IMDB CODE")

    express1 = r'<script src="https://guardahd.stream/ddl/tt(.*?)"'
    code = re.compile(express1, re.MULTILINE | re.DOTALL).findall(r.text)[0]
    
    return imdb("tt"+code)

def bing(parIn):
    import re
    video_urls = []
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }

    s = requests.Session()
    r = s.get(parIn, headers=headers)
    logga("FIND HOSTS FOR "+parIn)

    express = r'<iframe src="(.*?)"'
    link = re.compile(express, re.MULTILINE | re.DOTALL).findall(r.text)[0]
    if "assia" in link:
        return assia(link)
    
    video_urls.append(("ignore", "[COLOR red]NO LINK FOUND[/COLOR]"))
    return video_urls




def imdb(parIn):
    import re
    video_urls = []

    url="https://mostraguarda.stream/set-movie-a//"+parIn
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }

    s = requests.Session()
    r = s.get(url, headers=headers)
    logga("FIND HOSTS FOR "+parIn)
    jsonText='{"SetViewMode":"503","items":['
    numIt=0
    
    if "not found" in r.text:
        logga("NO LINK FOUND FOR "+parIn)
    else:
        express = r'<title>(.*?)</title>'
        title = re.compile(express, re.MULTILINE | re.DOTALL).findall(r.text)[0]
        
        
        
        express1 = r'<ul class="_player-mirrors">(.*?)</ul>'
        ret1 = re.compile(express1, re.MULTILINE | re.DOTALL).findall(r.text)[0]
        htmlFlat=ret1.replace("\n", '').replace("\r", '').replace("\t", '')
        express2 = r'data-link="(.*?)">(.*?)<\/li>'
        ret = re.compile(express2, re.MULTILINE | re.DOTALL).findall(htmlFlat)
        for (link, ep) in ret:
            if "Player 4K" not in ep:
                if link[0:2] == "//":
                    link = "https:"+link
                #logga('LINK-IMDB: '+link+" "+ep)
                if (numIt > 0):
                    jsonText = jsonText + ','    
                jsonText = jsonText + '{"title":"[COLOR lime]'+ep.strip()+'[/COLOR]","myresolve":"risolvi@@'+link+'",'
                jsonText = jsonText + '"thumbnail":"https://cdn3d.iconscout.com/3d/premium/thumb/watching-movie-4843361-4060927.png",'
                jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
                jsonText = jsonText + '"info":"'+title+'"}'
                numIt=numIt+1
    
    if numIt==0:
        jsonText = jsonText + '{"title":"[COLOR red]NO HOST FOUND[/COLOR]","link":"ignore",'
        jsonText = jsonText + '"thumbnail":"https://cdn3d.iconscout.com/3d/premium/thumb/watching-movie-4843361-4060927.png",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"NO INFO"}'

    jsonText = jsonText + "]}"
    logga('JSON-IMDB: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls

def createSportMenu(parIn=""):
    if parIn=="nopay":
        return nopayMenu()
    if parIn=="zonline":
        return sportsonlineMenu()
    if parIn=="daddy":
        return daddyLiveMenu()
    if parIn=="platin":
        return platinumMenu()
    if parIn=="ppv":
        return ppvMenu()

def ppvMenu():
    import json
    from datetime import datetime
    video_urls = []

    # Scarica la pagina
    page = requests.get("https://ppvs.su/api/streams").text
    arrJ = json.loads(page)

    arrEv = []

    # Prima parte: costruzione dell'array ordinabile
    for event in arrJ["streams"]:
        sport = event["category"]
        if sport == "Football":
            sport =" Calcio"
        for gara in event["streams"]:
            comp = gara["tag"]
            match = gara["name"]
            poster = gara["poster"]
            url = gara["iframe"]
            date = gara["starts_at"]

            arrEv.append(f"{sport}@@{date}@@{comp}@@{match}@@{poster}@@{url}")

    # Ordina come in PHP
    arrEv.sort()

    # Seconda parte: costruzione struttura finale
    toRet = {"SetViewMode": "50", "channels": []}

    numGroup = -1
    oldSport = ""
    numIt = 0

    for row in arrEv:
        sport, date, comp, match, poster, url = row.split("@@")

        # PHP: $quando = date("Y-m-d H:i", intval($date)+3600)
        quando = datetime.utcfromtimestamp(int(date) + 3600).strftime("%Y-%m-%d %H:%M")

        if sport == "24/7 Streams":
            continue
        
        
        # Nuovo gruppo di sport
        if oldSport != sport:
            numGroup += 1
            oldSport = sport

            toRet["channels"].append({
                "name": f"[COLOR gold]{sport}[/COLOR]",
                "thumbnail": "https://thumbs.dreamstime.com/b/logos-d-annata-misto-di-sport-di-vettore-73688323.jpg",
                "fanart": "https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",
                "SetViewMode": "50",
                "items": []
            })
            numIt = 0

        # Aggiunge item evento
        toRet["channels"][numGroup]["items"].append({
            "title": f"[COLOR gold]{quando}[/COLOR] [COLOR aqua]{comp}[/COLOR] [COLOR lime]{match}[/COLOR]",
            "myresolve": f"ppv@@{url}",
            "thumbnail": poster,
            "fanart": "https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",
            "info": match
        })

        numIt += 1

    # Output finale JSON formattato
    jsonText=json.dumps(
        toRet,
        ensure_ascii=False,
        indent=4
    )
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls


def platinumMenu():
    video_urls = []

    url="https://www.platinsport.com/"
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    ret1 = s.get(url, headers=headers)
    htmlFlat=ret1.text.replace("\n", '').replace("\r", '').replace("\t", '')
    express2 = r'<td><img decoding="async" class="(.*?)" src="(.*?)" (.*?)/></td><td>(.*?)</td><td><a href="http://bc.vc/(.*?)/(.*?)" target="_blank" rel="noopener noreferrer">'
    #express2 = r'<td><img decoding="async" loading="lazy" class="(.*?)" src="(.*?)" (.*?)/></td><td>(.*?)</td><td><a href="http://bc.vc/(.*?)/(.*?)" target="_blank" rel="noopener noreferrer">'
    ret = re.compile(express2, re.MULTILINE | re.DOTALL).findall(htmlFlat)
    jsonText='{"SetViewMode":"51","items":['
    numIt=0
    for (par1, img, par2, tit, par3, link) in ret:
        if (numIt > 0):
            jsonText = jsonText + ','    
        newTit = re.sub('[^a-zA-Z0-9 \n\.]', 'I', tit)
        jsonText = jsonText + '{"title":"[COLOR lime]'+newTit.replace("II", 'I')+'[/COLOR]","myresolve":"platin@@'+link+'",'
        jsonText = jsonText + '"thumbnail":"'+img+'",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"'+tit+'"}'
        numIt=numIt+1
    
    if numIt==0:
        jsonText = jsonText + '{"title":"[COLOR red]NO MATCH FOUND[/COLOR]","link":"ignore",'
        jsonText = jsonText + '"thumbnail":"https://cdn3d.iconscout.com/3d/premium/thumb/watching-movie-4843361-4060927.png",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"NO INFO"}'

    jsonText = jsonText + "]}"
    logga('JSON-PLATIN: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls


def getSportLogo(sportName):
    toRet="https://autyzmwszkole.files.wordpress.com/2015/11/sport2.jpg"
    if (sportName=="Soccer" or sportName==" Calcio"):
        toRet="https://play-lh.googleusercontent.com/lsJjbVdV5fNzgVS9RALpiPxUWcZkHkCQAxD7I_26d-gGejt45r1SNZV5-lFBfQtcHg"
    if (sportName=="Cricket"):
        toRet="https://seeklogo.com/images/C/cricket-logo-DC6957DD66-seeklogo.com.png"
    if (sportName=="Tennis"):
        toRet="https://img.bestdealplus.com/ae04/kf/Hf448267801434196b98c876992ed9bc3Y.jpg";
    if (sportName=="MMA"):
        toRet="https://i.pinimg.com/originals/ac/00/d5/ac00d52d06acbbd6ce3af3777e785e23.jpg";
    if "Moto" in sportName or "moto" in sportName:
        toRet="https://i.pinimg.com/originals/c6/1d/d2/c61dd299176c82de8bde053331e76e17.jpg";
    if (sportName=="Golf"):
        toRet="https://chip-ing.com/wp-content/uploads/2021/10/Golfer_1-1170x10331-1-1024x904.png";
    if (sportName=="Baseball"):
        toRet="https://seeklogo.com/images/R/red-and-black-baseball-logo-BAE3744108-seeklogo.com.png";
    if (sportName=="Basketball" or sportName=="Basket"):
        toRet="https://i.pinimg.com/originals/97/b5/95/97b595b930ac325d7e03a2c0d84c265b.jpg";
    if "Hockey" in sportName:
        toRet="https://image.freepik.com/vettori-gratuito/distintivo-di-hockey-su-ghiaccio-logo-modello-di-torneo-della-squadra-emblema_7112-199.jpg";
    if "Combat"in sportName:
        toRet="https://pngimg.com/d/ufc_PNG75.png";
    if (sportName=="Cycling"):
        toRet="https://freepngimg.com/download/bike/23211-1-bike-ride-image.png";
    if (sportName=="Beach Soccer"):
        toRet="https://images.squarespace-cdn.com/content/v1/5a32532ae9bfdfec59a39d04/1516203783799-49KUS1XV4XH0174U1E5E/Beach+Soccer.png";
    if (sportName=="Darts"):
        toRet="https://img.freepik.com/free-vector/darts-game-emblem_109132-92.jpg";
    if (sportName=="Badminton"):
        toRet="https://banner2.cleanpng.com/20180324/fye/kisspng-badminton-shuttlecock-yonex-logo-sport-badminton-5ab6916c3415b0.2726775915219142202134.jpg";
    if (sportName=="Futsal"):
        toRet="https://images-platform.99static.com/2YNHyBVTpcMsiCsLid0oJkDtUkQ=/0x0:2000x2000/500x500/top/smart/99designs-contests-attachments/112/112918/attachment_112918109";
    if "Rugby" in sportName:
        toRet="https://image.freepik.com/vettori-gratuito/rugby-logo-american-logo-sport_7112-532.jpg"
    if "Aussie" in sportName:
        toRet="https://image.freepik.com/vettori-gratuito/rugby-logo-american-logo-sport_7112-532.jpg"
    if "Equestrian" in sportName or "Horse" in sportName:
        toRet="https://i.pinimg.com/originals/43/72/58/437258335411310ed156680a78f1b911.jpg"
    if (sportName=="Tennis da tavolo"):
        toRet="https://e7.pngegg.com/pngimages/783/738/png-clipart-table-tennis-racket-addicting-games-ping-pong-game-sports-thumbnail.png"
    if (sportName=="Chess"):
        toRet="https://i.pinimg.com/736x/3c/4f/18/3c4f1886e5b1d47f3126703fd20f56b7.jpg"
    if (sportName=="Pallamano" or sportName=="Handball"):
        toRet="https://png.pngitem.com/pimgs/s/19-197475_handball-logo-minis-handball-logo-hd-png-download.png"
    if (sportName=="Pallavolo" or sportName=="Volleyball"):
        toRet="https://cdn6.f-cdn.com/contestentries/1471562/33395594/5c789de756a88_thumb900.jpg"
    if (sportName=="WWE"):
        toRet="https://www.wrestling-news.net/wp-content/uploads/2019/04/WWE.png"
    if (sportName=="Snooker"):
        toRet="https://t3.ftcdn.net/jpg/03/20/04/28/360_F_320042878_AJvfy22rnAtFZ6msEOhXlGMM2hbCBXYC.jpg"
    if "Ski" in sportName:
        toRet="https://us.123rf.com/450wm/baldyrgan/baldyrgan1701/baldyrgan170100008/69262433-sci-simbolo-stilizzato-logo-o-emblema-modello.jpg?ver=6"
    if (sportName=="Boxe" or sportName=="Boxing" or sportName=="Pugilato"):
        toRet="https://image.freepik.com/vecteurs-libre/logo-graphique-insigne-boxe_24908-54891.jpg"
    if (sportName=="Lacrosse"):
        toRet="https://img0-placeit-net.s3-accelerate.amazonaws.com/uploads/stage/stage_image/30400/optimized_large_thumb_stage.jpg"
    if (sportName=="WaterPolo"):
        toRet="https://images.vexels.com/media/users/3/203460/isolated/preview/57a4cd98f07284a832f66e0c726e1e30-waterpolo-male-player-blue.png"
    if (sportName=="Biathlon"):
        toRet="https://skitrax.com/wp-content/uploads/2017/02/IBU-Logo.3-2017-01-22-at-6.55.22-AM.png"
    if (sportName=="Squash"):
        toRet="https://www.pngkit.com/png/full/206-2061953_squash-player-png.png"
    if (sportName=="Kick Volleyball"):
        toRet="https://i.pinimg.com/originals/4f/59/af/4f59af612f275a1420724dff57baecff.png"
    if "Sailing" in sportName or "Boating" in sportName:
        toRet="https://second-hand.decathlon.it/bundles/front/img/icons-sports/minis/canoeing.png"
	
    return toRet


def daddyLiveMenu():
    import re, datetime
    video_urls = []
    url="https://daddylivehd.sx/"
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    r = s.get(url, headers=headers)
    dataFile = r.text.replace("\n", "").replace("\r", "").replace("\t", "")
    arrDiv = dataFile.split("<h2")
    #logga("H2: "+str(len(arrDiv)))
    arrTemp = []
    logoSp="https://autyzmwszkole.files.wordpress.com/2015/11/sport2.jpg"
    cont=0
    okRow=0
    for div in arrDiv:
        cont=cont+1
        if cont==1:
            continue
        #logga ("DIV DADDY: "+div)
        if "background-color" in div:
            #logga ("OK BGR")
            express = r'>(.*?)</h2>'
            try:
                sportName = re.compile(express, re.MULTILINE | re.DOTALL).findall(div)[0]
                #logga("sportName: "+sportName)
                if sportName == "Soccer":
                    sportName = " Calcio"
                    okRow=1
            except:
                pass
            if okRow==0:
                continue
            logoSp=getSportLogo(sportName)
            arrH=div.split("<hr>")
            #logga("HR: "+str(len(arrH)))
            conta=0
            for hr in arrH:
                conta=conta+1
                if conta==1:
                    continue
                arrEv=hr.split("<span")
                titol=arrEv[0].replace("<strong>", "").replace("</strong>", "")
                #logga ("titolo: "+titol)
                if "<" in titol or len(titol) < 6:
                    continue
                hh = titol[0:2]
                mm = titol[3:5]
                dt = datetime.datetime(2000, 6, 10, int(hh), int(mm), 45)
                dt1 = dt + datetime.timedelta(hours=-3)
                newDate = dt1 + datetime.timedelta(minutes=-30)
                hh2=str(newDate.hour)
                if newDate.hour < 10:
                    hh2="0"+str(newDate.hour)
                mm2=str(newDate.minute)
                if newDate.minute < 10:
                    mm2="0"+str(newDate.minute)
                timeMatch=hh2+":"+mm2
                titolo=timeMatch+titol[5:]
                links=hr[len(titolo):]
                if "|" in links:
                    arrPP = links.split("|")
                    for tfgr in arrPP:
                        express = r'href="(.*)" target'
                        ret1 = re.compile(express, re.MULTILINE | re.DOTALL).findall(tfgr)
                        express = r'"noopener">(.*)</a>'
                        ret2 = re.compile(express, re.MULTILINE | re.DOTALL).findall(tfgr)
                        numRe=0
                        oldTit=""
                        for linkR in ret1:
                            if linkR.startswith("/extra"):
                                logga("NO BUONO")
                            else:
                                try:
                                    titR=ret2[numRe]
                                    oldTit=titR
                                except:
                                    logga("NO TIT FOR "+sportName+" - "+titolo+" ["+str(numRe))
                                    titR=oldTit

                                arrTemp.append(sportName+"@@"+titolo+"@@"+logoSp+"@@"+linkR+"@@"+titR)
                                numRe=numRe+1
                else:
                    express = r'href="(.*)" target'
                    ret1 = re.compile(express, re.MULTILINE | re.DOTALL).findall(links)
                    express = r'"noopener">(.*)</a>'
                    ret2 = re.compile(express, re.MULTILINE | re.DOTALL).findall(links)
                    numRe=0
                    for linkR in ret1:
                        titR=ret2[numRe]
                        if linkR.startswith("/extra"):
                            logga("NO BUONO")
                        else:
                            arrTemp.append(sportName+"@@"+titolo+"@@"+logoSp+"@@"+linkR+"@@"+titR)
                            numRe=numRe+1

                

            
    jsonText='{"SetViewMode":"50","channels":['
    sorted(arrTemp)
    oldSport=""
    numCh=0
    numIt=0
    for row in arrTemp:
        arrRow=row.split("@@")        
        sport=arrRow[0]
        match=arrRow[1]
        logo=arrRow[2]
        link=arrRow[3]
        ch=arrRow[4]
        if oldSport != sport:
            if (numCh > 0):
                jsonText = jsonText + ']},'    
            jsonText = jsonText + '{"name":"[COLOR gold]'+sport.strip()+'[/COLOR] ",'
            jsonText = jsonText + '"thumbnail":"'+logo+'",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"SetViewMode":"51","items":['
            oldSport = sport
            numIt=0
            numCh=numCh+1
        if (numIt > 0):
            jsonText = jsonText + ','    
        
        jsonText = jsonText + '{"title":"[COLOR lime]'+match.strip()+'[/COLOR] [COLOR orange]'+ch+'[/COLOR]",'
        jsonText = jsonText + '"myresolve":"daddy@@https://dlhd.sx'+link+'",'
        jsonText = jsonText + '"thumbnail":"'+logo+'",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"by MandraKodi"}'
        numIt=numIt+1
    
    if (numIt > 0):
        jsonText = jsonText + ']}' 

    
    if numIt==0:
        jsonText = '{"SetViewMode":"503","items":[{"title":"[COLOR red]NO MATCH FOUND[/COLOR]","link":"ignore",'
        jsonText = jsonText + '"thumbnail":"https://www.avis.it/wp-content/uploads/2018/06/Sport_balls.png",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"NO INFO"}'

    jsonText = jsonText + "]}"
    logga('JSON-DADDY: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls


def sportsonlineMenu():
    import datetime
    video_urls = []

    arrWeek={"SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"}
    url="https://sportsonline.st/prog.txt"
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    r = s.get(url, headers=headers)
    jsonText='{"SetViewMode":"500","channels":['
    #arrLine = r.text.splitlines
    numIt=0
    numCh=0
    start=0
    for line in r.text.splitlines():
        if line == "" or line[0:1]== "." or line[0:1]== "|":
            continue
        logga("ROW: "+line)
        for day in arrWeek:
            if day in line:
                if (numCh > 0):
                    jsonText = jsonText + ']},'    
                jsonText = jsonText + '{"name":"[COLOR gold]'+line.strip()+'[/COLOR] ",'
                jsonText = jsonText + '"thumbnail":"https://freepngimg.com/download/calendar/4-2-calendar-png-hd.png",'
                jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
                jsonText = jsonText + '"SetViewMode":"51","items":['
                numIt=0
                numCh=numCh+1
                start=1
        if start==1:
            if "|" in line:
                arrT=line.split("|")
                titolMatch=arrT[0].replace(" x ", " vs ").replace(" @ ", " vs ")
                hh = titolMatch[0:2]
                mm = titolMatch[3:5]
                titMatch=titolMatch[6:].strip()
                newTit = re.sub('[^a-zA-Z0-9 \n\.]', '*', titMatch)
                timeMatch="00:00"
                try:
                    dt = datetime.datetime(2000, 6, 10, int(hh), int(mm), 45)
                    newDate = dt + datetime.timedelta(hours=1)
                    hh2=str(newDate.hour)
                    if newDate.hour < 10:
                        hh2="0"+str(newDate.hour)
                    mm2=str(newDate.minute)
                    if newDate.minute < 10:
                        mm2="0"+str(newDate.minute)
                    timeMatch=hh2+":"+mm2
                except:
                    pass
                linkMatch=arrT[1].strip()
                arrL=linkMatch.split("/")
                tit=arrL[-1].replace(".php", "")
                if (numIt > 0):
                    jsonText = jsonText + ','    
                
                jsonText = jsonText + '{"title":"[COLOR gold]'+timeMatch+'[/COLOR] [COLOR lime]'+newTit.strip()+'[/COLOR] [COLOR aqua]('+tit+')[/COLOR]",'
                #jsonText = jsonText + '"myresolve":"spon@@'+linkMatch.replace("v2.sportsonline", "sportsonline")+'",'
                jsonText = jsonText + '"myresolve":"spon@@'+linkMatch+'",'
                jsonText = jsonText + '"thumbnail":"https://www.avis.it/wp-content/uploads/2018/06/Sport_balls.png",'
                jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
                jsonText = jsonText + '"info":"by MandraKodi"}'
                numIt=numIt+1
            #except:
                #logga("ERRORE")
                #pass
    if (numIt > 0):
        jsonText = jsonText + ']}' 


    
    
    
    if numIt==0:
        jsonText = '{"SetViewMode":"503","items":[{"title":"[COLOR red]NO MATCH FOUND[/COLOR]","link":"ignore",'
        jsonText = jsonText + '"thumbnail":"https://www.giardiniblog.it/wp-content/uploads/2018/12/serie-tv-streaming.jpg",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"NO INFO"}'

    jsonText = jsonText + "]}"
    logga('JSON-ZONLINE: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls

def nopayMenu(parIn=""):
    import re
    video_urls = []

    url="https://nopay2.info/"

    
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    r = s.get(url, headers=headers)
    
    express1 = r'<div class="card text(.*?)>(.*?)</div></div></div>'
    htmlFlat=r.text.replace("\n", "").replace("\r", "").replace("\t", "")
    #logga("HTML\n"+htmlFlat)
    ret1 = re.compile(express1, re.MULTILINE | re.DOTALL).findall(htmlFlat)
    #logga("TROVATI "+str(len(ret1[0]))+" RECORDS")
    arrTemp = []
    for card, div in ret1:
        express2 = r'<div class="card-header" style="background-image: (.*?)">(.*?)</div>'
        ret2 = re.compile(express2, re.MULTILINE | re.DOTALL).findall(div)
        immagine=""
        evento=""
        for (img, event) in ret2:
            immagine=img.replace("url(", "").replace(");", "")
            evento=event.replace("\n", "").replace("\r", "").replace("\t", "").replace("<br>", "")

        expressDay = r'<div class="card-body"><p>(.*?)</p>'
        day = re.compile(expressDay, re.MULTILINE | re.DOTALL).findall(div)[0]
        if "</br>" in day:
            arrD=day.split("</br>")
            day=arrD[0]
        express3 = r'href="\/embe.php\?id=(.*?)" target="_blank" class="btn btn-primary"><i class="flag (.*?)" style="vertical-align: baseline;"></i>(.*?)</a>'
        ret3 = re.compile(express3, re.MULTILINE | re.DOTALL).findall(div)
        for (ch, flag, tit) in ret3:
            row=day.strip()+"@@"+evento.strip()+"@@"+tit+"@@"+ch+"@@https://nopay2.info/"+immagine
            arrTemp.append(row)
            
    
    sorted(arrTemp)
    numIt=0
    oldDay=""
    numCh=0
    jsonText='{"SetViewMode":"500","channels":['
    for row in arrTemp:
        arrRow=row.split("@@")
        day=arrRow[0]
        evento=arrRow[1]
        tit=arrRow[2]
        ch=arrRow[3]
        img=arrRow[4]
        if (oldDay != day):
            if (numCh > 0):
                jsonText = jsonText + ']},'    
            jsonText = jsonText + '{"name":"[COLOR gold]'+day+'[/COLOR] ",'
            jsonText = jsonText + '"thumbnail":"https://freepngimg.com/download/calendar/4-2-calendar-png-hd.png",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"SetViewMode":"51","items":['
            oldDay = day
            numIt=0
            numCh=numCh+1
        if (numIt > 0):
            jsonText = jsonText + ','    
        
        jsonText = jsonText + '{"title":"[COLOR lime]'+evento.strip()+'[/COLOR] [COLOR aqua]('+tit+')[/COLOR]",'
        jsonText = jsonText + '"myresolve":"wigi@@https://nopay2.info/embe.php?id='+ch+'",'
        jsonText = jsonText + '"thumbnail":"'+img+'",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"by MandraKodi"}'
        numIt=numIt+1

    if (numIt > 0):
        jsonText = jsonText + ']}' 

    if numIt==0:
        jsonText = '{"SetViewMode":"503","items":[{"title":"[COLOR red]NO MATCH FOUND[/COLOR]","link":"ignore",'
        jsonText = jsonText + '"thumbnail":"https://res.9appsinstall.com/group4/M00/51/F1/ghoGAFy4guuAJwiKAAAquIT5LH0862.png",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"NO INFO"}'

    jsonText = jsonText + "]}"
    logga('JSON-NOPAY: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls
    
def menuIstorm(parIn=""):
    video_urls = []
    
    urlPage="https://antenasports.ru/channels.php"
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }

    s = requests.Session()
    r = s.get(urlPage, headers=headers)
    
    express2 = r'<div class="grid-item"><a href="(.*?)" target="_blank" rel="noopener"><span style="(.*?)"><strong>(.*?)</strong>'
    ret = re.compile(express2, re.MULTILINE | re.DOTALL).findall(r.text)
    
    lst = []
    x=1
    for (link, id, tito) in ret:
        if (x > 2):
            lst.append(tito+"@@"+link)
        x=x+1
    lst.sort()
    jsonText='{"SetViewMode":"503","items":['
    x=1
    for (row) in lst:
        arrL=row.split("@@")
        tito=arrL[0]
        link=arrL[1]
        if (x > 1):
            jsonText = jsonText + ','    
        jsonText = jsonText + '{"title":"[COLOR lime]'+tito+'[/COLOR]","myresolve":"antena@@https://antenasports.ru'+link+'",'
        jsonText = jsonText + '"thumbnail":"https://upload.wikimedia.org/wikipedia/commons/d/db/Sports_portal_bar_icon.png",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"CHANNEL '+tito+'"}'
        x=x+1
    
    jsonText = jsonText + "]}"
    logga('JSON-ANTENA: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls

def taxi(parIn):
    import re
    video_urls = []

    sc_url="https://raw.githubusercontent.com/mandrakodi/mandrakodi.github.io/main/data/taxi_url.txt"
    scUrl=makeRequest(sc_url)
    url=scUrl.replace("\n", '')+"stream/"+parIn

    #url="https://guardaserie.events/serietv/"+parIn+".html"
    
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
    page=r.text.replace("\n", "").replace("\r", "").replace("\t", "")
    #logga("FIND HOSTS AT "+url+"\n"+page)
    ret1 = "by @mandrakodi"
    express1 = r'<title>(.*?)</title>'
    ret1 = re.compile(express1, re.MULTILINE | re.DOTALL).findall(page)[0]

    express2 = r'<a href="#" allowfullscreen data-link="(.*?)" id="(.*?)" data-num="(.*?)" data-title="(.*?)">\d+</a>(.*?)</li>'
    ret = re.compile(express2, re.MULTILINE | re.DOTALL).findall(page)
    jsonText='{"SetViewMode":"503","items":['
    numIt=0
    for (link, id, ep, tito, mirror) in ret:
        #express3 = r'<a href="#" class="mr" data-m="dropload" data-link="(.*?)">'
        #express3 = r'<a href="#" class="mr" data-m="supervideo" data-link="(.*?)">'
        express3 = r'<a href="#" class="mr" data-link="(.*?)">'
        ret2 = re.compile(express3, re.MULTILINE | re.DOTALL).findall(mirror)[0]
        if "supervideo" in ret2: 
            ret2 = re.compile(express3, re.MULTILINE | re.DOTALL).findall(mirror)[1]
        link=ret2
        if (numIt > 0):
            jsonText = jsonText + ','  
        
        jsonText = jsonText + '{"title":"[COLOR lime]'+ep+'[/COLOR]","myresolve":"proData@@'+link+'",'
        jsonText = jsonText + '"thumbnail":"https://www.giardiniblog.it/wp-content/uploads/2018/12/serie-tv-streaming.jpg",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"'+tito.replace('"', '')+'"}'
        numIt=numIt+1

    if numIt==0:
        jsonText = jsonText + '{"title":"[COLOR red]NO HOST FOUND[/COLOR]","link":"ignore",'
        jsonText = jsonText + '"thumbnail":"https://www.giardiniblog.it/wp-content/uploads/2018/12/serie-tv-streaming.jpg",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"NO INFO"}'

    jsonText = jsonText + "]}"
    logga('JSON-TAXI: '+jsonText)
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls

def platin(parIn=None):
    video_urls = []
    randomUa=getRandomUA()
    
    headers = {
        'user-agent': randomUa
    }

    s = requests.Session()
    r = s.get(parIn, headers=headers)
    logga("FIND HOSTS")
    ret1 = "by @mandrakodi"
    
    express1 = r'<a href="acestream://(.*?)" rel="nofollow">(.*?)</a>'
    ret1 = re.compile(express1, re.MULTILINE | re.DOTALL).findall(r.text)

    for aceId, aceTit in ret1:
        video_urls.append(("acestream://"+aceId, "[COLOR lime]"+aceTit+" (ACE)[/COLOR]"))
    
    express2 = r'<a href="(.*?)" target="_blank" rel="noopener"><button'
    ret2 = re.compile(express2, re.MULTILINE | re.DOTALL).findall(r.text)
    numL=0
    for linkTmp in ret2:
        logga("TRY FOR "+linkTmp)
        try:
            video_url = proData(linkTmp.replace(" ", ""), 1)
            numL=numL+1
            video_urls.append((video_url, "[COLOR aqua]STREAM "+str(numL)+"[/COLOR]"))
        except:
            pass
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
        logga('OK REQUEST FROM '+url)
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
    video_urls = []
    page_in="https://vudeo.ws/"+parIn+".html"
    page_data = requests.get(page_in,headers={'user-agent':'iPad','accept':'*/*','referer':page_in}).content

    if PY3:
        page_data = page_data.decode('utf-8')
    nf = preg_match(page_data, '<b>File Not Found</b>')
    if nf != "":
        img = "https://www.online-tech-tips.com/wp-content/uploads/2019/08/cropped-video-not-found.png"
        video_urls.append(("ignore", "[COLOR red]VIDEO NOT FOUND[/COLOR]", "Video non trovato", img))
        return video_urls
    src = preg_match(page_data, 'sources: \["(.*?)"\]')
    tit = preg_match(page_data, '<title>(.*?)<\/title>')
    img = preg_match(page_data, 'poster: "(.*?)"')

    video_urls.append((src+"|referer="+page_in, "[COLOR lime]PLAY VIDEO[/COLOR]", tit.replace("Watch", ""), img))
    video_urls.append((src+"|referer="+page_in+"&verifypeer=false", "[COLOR orange]PLAY VIDEO[/COLOR]", tit.replace("Watch", ""), img))
    return video_urls

def voe(parIn):
    import base64
    logga('VOE PAGE: '+parIn)
    page_data = requests.get(parIn,headers={'user-agent':'iPad','accept':'*/*','referer':parIn}).content
    if PY3:
        page_data = page_data.decode('utf-8')

    logga ("VOE ==> "+page_data)
    tit = preg_match(page_data, '<h1 class="mt-1">(.*?)<span')
    src = preg_match(page_data, "'hls': '(.*?)'")
    src1 = preg_match(page_data, "'mp4': '(.*?)'")

    video_urls = []
    video_urls.append((base64.b64decode(src).decode("utf-8")+"|referer="+parIn, "[COLOR lime]PLAY VIDEO[/COLOR]", tit.replace(".mp4", "")))
    video_urls.append((base64.b64decode(src1).decode("utf-8")+"|referer="+parIn, "[COLOR gold]PLAY VIDEO[/COLOR]", tit.replace(".mp4", "")))
    return video_urls

def supervideo(page_url):
    import jsunpack, ast
    logga("url=" + page_url)
    video_urls = []
    # data = httptools.downloadpage(page_url).data
    data  = downloadHttpPage(page_url, headers={'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36','referer':page_url})
    logga("supervideo: " + data)

    code_data = find_single_match(data, """<script type=["'].*text/javascript["']>(eval.*)""")
    if code_data:
        code = jsunpack.unpack(code_data)
        logga("unpack: " + code)
        # corrections
        if 'file' in code and not '"file"'in code: code = code.replace('file','"file"')
        if 'label' in code and not '"label"'in code: code = code.replace('label','"label"')

        match = find_single_match(code, r'sources:(\[[^]]+\])')
        lSrc = ast.literal_eval(match)

        # lQuality = ['360p', '720p', '1080p', '4k'][:len(lSrc)-1]
        # lQuality.reverse()

        for source in lSrc:
            quality = source['label'] if 'label' in source else 'auto'
            tit = source['file'].split('.')[-1] 
            src =  source['file']
            arrTmp=src.split(",")
            newSrc=arrTmp[0]+arrTmp[1]+"/index-v1-a1.m3u8"
            video_urls.append((newSrc+"|Referer=https://supervideo.tv/&Origin=https://supervideo.tv&User-Agent=iPad", "[COLOR gold]PLAY VIDEO[/COLOR]", tit.replace(".mp4", "")))
    else:
        logga ("NO PACKED")
        matches = find_multiple_matches(data, r'src:\s*"([^"]+)",\s*type:\s*"[^"]+"(?:\s*, res:\s(\d+))?')
        for url, quality in matches:
            if url.split('.')[-1] != 'm3u8':
                video_urls.append([url, url.split('.')[-1] + ' [' + quality + '] [SuperVideo]'])
            else:
                video_urls.append([url, url.split('.')[-1]])

    return video_urls

def hunterjs(parIn):
    video_urls = []
    
    _0xce1e="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
    def duf(d,e,f):
        g = list(_0xce1e)
        h = g[0:e]
        i = g[0:f]
        d = list(d)[::-1]
        j = 0
        for c,b in enumerate(d):
            if b in h:
                j = j + h.index(b)*e**c
    
        k = ""
        while j > 0:
            k = i[j%f] + k
            j = (j - (j%f))//f
    
        return int(k) or 0
    
    def hunter(h,u,n,t,e,r):
        r = "";
        i = 0
        while i < len(h):
            j = 0
            s = ""
            while h[i] is not n[e]:
                s = ''.join([s,h[i]])
                i = i + 1
    
            while j < len(n):
                s = s.replace(n[j],str(j))
                j = j + 1
    
            r = ''.join([r,''.join(map(chr, [duf(s,e,10) - t]))])
            i = i + 1
    
        return r


    logga('HUNTER PAGE: '+parIn)
    page_data = requests.get(parIn,headers={'user-agent':'iPad','accept':'*/*','referer':parIn}).content

    if PY3:
        page_data = page_data.decode('utf-8')
    
    flatPage = page_data.replace("\n", "").replace("\r", "").replace("\t", "")
    tit = preg_match(flatPage, '<div id="player"><\/div><script>(.*?)\)\)<\/script>')
    logga("HUNTER CODE: "+tit)
    if tit == "":
        video_urls.append(("ignore", "[COLOR red]NO VIDEO FOUND[/COLOR]"))
        return video_urls
    
    sd=tit.split("(")
    code = sd[-1]
    logga("HUNTER CODE2: "+code)

    #code = 'YYmojrWojmWojYjojmmojYaojrWoYProjYaojYjojYYojYaorPaojmmoYarorYjoYarojmrojrjojYjorPPojrrojmWojYaojYjoYaroYWjoYWaoYarojjroYYmojYYojmYojrroYarojYWojYYorPaojjmojmYojrmoYarorYjoYarojYjojmYojrWoYarorrrojYYorPaojYWojYWojrmoYProraYojYYorPaojjmojmYojrmoYWjojjroYYmojrYojYaojrjojrmorPPojmYorYmoYaroYWrojmaojrrojrrojYWojrYorYmoYPjoYPjorPPorPaojrmojrmojmWojmYojYrojYaojrmojmYoYProrPPojYYojrjorPWoYPjojmaojYYojrYoYPjojrrojrYojYjormYoYPjojYWojYYorPaojjmojYYojmWojrYojrroYProjYrormmojrjormWoYWroYPmoYYmojmaojmYojmWojmjojmaojrrorYmoYaroYWroYPWoYPaoYPaoYWmoYWroYPmoYYmojrWojmWojmmojrrojmaorYmoYaroYWroYPWoYPaoYPaoYWmoYWroYPmoYYmojYWorPaojrmojmYojYjojrrorjYojmmorYmoYaroYWroYaWojYWojYYorPaojjmojmYojrmoYWroYPmoYYmorPaojrjojrrojYaoraYojYYorPaojjmorYmoYarojmrorPaojYYojrYojmYoYPmoYYmojYWojYYorPaojjmorjYojYjojYYojmWojYjojmYorYmoYarojrrojrmojrjojmYoYPmoYYmojYrojmWojYrojmYoraWojjmojYWojmYorYmoYaroYaaorPaojYWojYWojYYojmWorPPorPaojrrojmWojYaojYjoYPjojrPoYPYojYrojYWojmYojmjoraPorajorjaoYaaoYPmoYYmojYWojYYojrjojmjojmWojYjojrYorYmoYarojjroYWrorPPojYaojrmojmYoYWrorYmoYarorWWorjaojmYojraojmYojYYoraaojmYojYYojmYorPPojrrojYaojrmorPmojjaoYPmoYYmojYrojmYojmmojmWorPaorPPojYaojYjojrrojrmojYaojYYorYmoYarojjroYYmojrYojmYojmYojYmorPWorPaojrmorYmoYaroYWroYaWoYPaoYPWormYorrmorrWorrWoYWroYPmoYYmorPWojrjojrrojrrojYaojYjojrYorYmoYaroYWroYaWorrWorrWorrWoYWroYYmojjaoYYmojjaoYWaorYYoYYmojjaorYYoYYmojrYojmYojrroraWojmWojYrojmYojYaojrjojrroYWjojmrojrjojYjorPPojrrojmWojYaojYjoYWjoYWaoYarojjroYYmoYaPoYWjoYWroYProjYrojmYojmmojmWorPaoYPYorPPojYaojYjojrrojrmojYaojYYoYPYojYYojmYojmrojrroYPYojYWorPaojYjojmYojYYoYWroYWaorWWoYWrorPaojYWojYWojmYojYjojmmoYWrorPmoYWjoYWrorYrorPWojrjojrrojrrojYaojYjoYarojrYojrrojjmojYYojmYorYjoYaaoYaaoYarojrrojjmojYWojmYorYjoYaaorPWojrjojrrojrrojYaojYjoYaaoYarorPPojYYorPaojrYojrYorYjoYaaojYrojmYojmmojmWorPaoYPYorPPojYaojYjojrrojrmojYaojYYoYPYorPWojrjojrrojrrojYaojYjoYarojYrojmYojmmojmWorPaoYPYorPPojYaojYjojrrojrmojYaojYYoYPYojmWorPPojYaojYjoYarojmYojYjorPaorPWojYYojmYojmmoYaaoYarojmmorPaojrrorPaoYPYojmaojmmoYPYojmWojYjojmmojmWorPPorPaojrrojYaojrmorYjoYaaoYaaoYarorPaojrmojmWorPaoYPYojYYorPaorPWojmYojYYorYjoYaaojmaojmmoYPYojmWojYjojmmojmWorPPorPaojrrojYaojrmoYaaorYaorYrorPaoYarojmaojrmojmYojmrorYjoYaaojmaojrrojrrojYWojrYorYmoYPjoYPjojmjojmWojraojmYojYrojmYojrmojmYojmmojmmojmWojrrojrYojrrojrmojmYorPaojYrojrYoYProjrPojjmojjYoYPjojYjorPWorPaoYaaoYarojrrorPaojrmojmjojmYojrrorYjoYaaorProrPWojYYorPaojYjojYmoYaaorYaorYrojmWojYrojmjoYarojrYojrmorPPorYjoYaaojmaojrrojrrojYWojrYorYmoYPjoYPjojmjojmWojraojmYojYrojmYojrmojmYojmmojmmojmWojrroYProjmYojrjoYPjoYPPoYProjYWojYjojmjoYaaoYarojrWojmWojmmojrrojmaorYjoYaaoYPWormmoYPaojYWojrPoYaaoYarojmaojmYojmWojmjojmaojrrorYjoYaaoYPPoYPaojYWojrPoYaaoYaroYPjorYaorYroYPjorPaorYaorYroYPjorPWojrjojrrojrrojYaojYjorYaoYWroYWaoYYmojjaoYPmoYarormroYPaoYPaoYPaoYWaorYYoYYmo",58,"mYrjaWPoi",47,7,24'
    code_list = code.split(',')
    for idx,code in enumerate(code_list):
        if code.isdigit():
            code_list[idx] = int(code)
        else:
            code_list[idx] = code.replace('\"','')
    
    result = hunter(*code_list)
    logga("HUNTER CODE3: "+result)
    link = preg_match(result, "source: '(.*?)'")
    logga("HUNTER LINK: "+link)
    video_urls.append((link+"|referer="+parIn, "[COLOR lime]PLAY VIDEO[/COLOR]"))

    return video_urls

def nflinsider(parIn):
    video_urls = []
    #urlPage="https://basketball-video.com/"+parIn
    urlPage="https://nbaontv.com/"+parIn
    page_data = requests.get(urlPage,headers={'user-agent':'iPad','accept':'*/*','referer':'https://basketball-video.com/'}).content

    if PY3:
        page_data = page_data.decode('utf-8')
    
    #link = preg_match(page_data, '<iframe allowfullscreen="" frameborder="0" height="315" src="(.*?)"')
    link = preg_match(page_data, 'frameborder="0" height="315" src="(.*?)"')
    if (link.startswith("//")):
        link="https:"+link
    logga("NFLINSIDER LINK: "+link)
    if ".mkv" in link:
        video_urls.append((link+"|referer=https://basketball-video.com/", "[COLOR lime]PLAY VIDEO[/COLOR]", "PLAY VIDEO"))
        return video_urls
    return urlsolver(link)


def vavoo_groups():
    #return ["Italy","Albania","Arabia","Balkans","Bulgaria","France","Germany","Netherlands","Poland","Portugal","Romania","Russia","Spain","Turkey","United Kingdom"]
    return ["Italy","France","Germany","Spain","United Kingdom"]

def get_channels(parIn='Italy'):
    resolver = VavooResolver()
    
    signature = resolver.getAuthSignature()
    headers = {
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "accept-encoding": "gzip",
        "mediahubmx-signature": signature
    }
    all_channels = []
    #for group in vavoo_groups():
    cursor = 0
    while True:
        data = {
            "language": "de",
            "region": "AT",
            "catalogId": "iptv",
            "id": "iptv",
            "adult": True,
            "search": "",
            "sort": "name",
            "filter": {"group": parIn},
            "cursor": cursor,
            "clientVersion": "3.0.2"
        }
        urlChList="https://vavoo.to/mediahubmx-catalog.json"
        # logga("URL CH_LIST: "+urlChList)
        resp = requests.post(urlChList, json=data, headers=headers, timeout=10)
        r = resp.json()
        logga ("VAVOO_CH_JSON: "+resp.text)
        items = r.get("items", [])
        all_channels.extend(items)
        cursor = r.get("nextCursor")
        if not cursor:
            break
    return all_channels


def vavooChList(parIn='Italy'):
    # logga (parIn+" SEARCH CHANNELS")
    if parIn == "UK":
        parIn = "United Kingdom"
    all_channels = get_channels(parIn)
    jsonText='{"SetViewMode":"51","items":['
    numIt=0
    for ch in all_channels:
        name = ch.get("name", "SenzaNome")
        url = ch.get("url", "")
        group = ch.get("group", "")
        if url:
            if (numIt > 0):
                jsonText = jsonText + ','    
            jsonText = jsonText + '{"title":"[COLOR lime]'+name+'[/COLOR]","myresolve":"vavooPlay@@'+url+'",'
            jsonText = jsonText + '"thumbnail":"https://lh3.googleusercontent.com/8ipMPaLb6545V3lrEUPozHUuBu09SLJaCTEG1OxawiJ8a_c79SEDCSlhFRr32VDMHw=h300",'
            jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
            jsonText = jsonText + '"info":"'+name+'"}'
            numIt=numIt+1    
    
    if numIt==0:
        jsonText = '{"SetViewMode":"503","items":[{"title":"[COLOR red]NO CHANNEL FOUND[/COLOR]","link":"ignore",'
        jsonText = jsonText + '"thumbnail":"https://www.giardiniblog.it/wp-content/uploads/2018/12/serie-tv-streaming.jpg",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"NO INFO"}'

    jsonText = jsonText + "]}"
    
    
    
    # logga('JSON-VAVOOCH: '+jsonText)
    video_urls= []
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls


class VavooResolver:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MediaHubMX/2'
        })

    def getAuthSignature(self):
        headers = {
            "user-agent": "okhttp/4.11.0",
            "accept": "application/json",
            "content-type": "application/json; charset=utf-8",
            "content-length": "1106",
            "accept-encoding": "gzip"
        }
        data = {
            "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
            "reason": "app-blur",
            "locale": "de",
            "theme": "dark",
            "metadata": {
                "device": {
                    "type": "Handset",
                    "brand": "google",
                    "model": "Nexus",
                    "name": "21081111RG",
                    "uniqueId": "d10e5d99ab665233"
                },
                "os": {
                    "name": "android",
                    "version": "7.1.2",
                    "abis": ["arm64-v8a", "armeabi-v7a", "armeabi"],
                    "host": "android"
                },
                "app": {
                    "platform": "android",
                    "version": "3.1.20",
                    "buildId": "289515000",
                    "engine": "hbc85",
                    "signatures": ["6e8a975e3cbf07d5de823a760d4c2547f86c1403105020adee5de67ac510999e"],
                    "installer": "app.revanced.manager.flutter"
                },
                "version": {
                    "package": "tv.vavoo.app",
                    "binary": "3.1.20",
                    "js": "3.1.20"
                }
            },
            "appFocusTime": 0,
            "playerActive": False,
            "playDuration": 0,
            "devMode": False,
            "hasAddon": True,
            "castConnected": False,
            "package": "tv.vavoo.app",
            "version": "3.1.20",
            "process": "app",
            "firstAppStart": 1743962904623,
            "lastAppStart": 1743962904623,
            "ipLocation": "",
            "adblockEnabled": True,
            "proxy": {
                "supported": ["ss", "openvpn"],
                "engine": "ss",
                "ssVersion": 1,
                "enabled": True,
                "autoServer": True,
                "id": "pl-waw"
            },
            "iap": {
                "supported": False
            }
        }
        try:
            resp = self.session.post("https://www.vavoo.tv/api/app/ping", json=data, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json().get("addonSig")
        except Exception as e:
            print(f"Errore nel recupero della signature: {e}")
            return None

    def gettsSignature(self):
        vec = {"vec": "9frjpxPjxSNilxJPCJ0XGYs6scej3dW/h/VWlnKUiLSG8IP7mfyDU7NirOlld+VtCKGj03XjetfliDMhIev7wcARo+YTU8KPFuVQP9E2DVXzY2BFo1NhE6qEmPfNDnm74eyl/7iFJ0EETm6XbYyz8IKBkAqPN/Spp3PZ2ulKg3QBSDxcVN4R5zRn7OsgLJ2CNTuWkd/h451lDCp+TtTuvnAEhcQckdsydFhTZCK5IiWrrTIC/d4qDXEd+GtOP4hPdoIuCaNzYfX3lLCwFENC6RZoTBYLrcKVVgbqyQZ7DnLqfLqvf3z0FVUWx9H21liGFpByzdnoxyFkue3NzrFtkRL37xkx9ITucepSYKzUVEfyBh+/3mtzKY26VIRkJFkpf8KVcCRNrTRQn47Wuq4gC7sSwT7eHCAydKSACcUMMdpPSvbvfOmIqeBNA83osX8FPFYUMZsjvYNEE3arbFiGsQlggBKgg1V3oN+5ni3Vjc5InHg/xv476LHDFnNdAJx448ph3DoAiJjr2g4ZTNynfSxdzA68qSuJY8UjyzgDjG0RIMv2h7DlQNjkAXv4k1BrPpfOiOqH67yIarNmkPIwrIV+W9TTV/yRyE1LEgOr4DK8uW2AUtHOPA2gn6P5sgFyi68w55MZBPepddfYTQ+E1N6R/hWnMYPt/i0xSUeMPekX47iucfpFBEv9Uh9zdGiEB+0P3LVMP+q+pbBU4o1NkKyY1V8wH1Wilr0a+q87kEnQ1LWYMMBhaP9yFseGSbYwdeLsX9uR1uPaN+u4woO2g8sw9Y5ze5XMgOVpFCZaut02I5k0U4WPyN5adQjG8sAzxsI3KsV04DEVymj224iqg2Lzz53Xz9yEy+7/85ILQpJ6llCyqpHLFyHq/kJxYPhDUF755WaHJEaFRPxUqbparNX+mCE9Xzy7Q/KTgAPiRS41FHXXv+7XSPp4cy9jli0BVnYf13Xsp28OGs/D8Nl3NgEn3/eUcMN80JRdsOrV62fnBVMBNf36+LbISdvsFAFr0xyuPGmlIETcFyxJkrGZnhHAxwzsvZ+Uwf8lffBfZFPRrNv+tgeeLpatVcHLHZGeTgWWml6tIHwWUqv2TVJeMkAEL5PPS4Gtbscau5HM+FEjtGS+KClfX1CNKvgYJl7mLDEf5ZYQv5kHaoQ6RcPaR6vUNn02zpq5/X3EPIgUKF0r/0ctmoT84B2J1BKfCbctdFY9br7JSJ6DvUxyde68jB+Il6qNcQwTFj4cNErk4x719Y42NoAnnQYC2/qfL/gAhJl8TKMvBt3Bno+va8ve8E0z8yEuMLUqe8OXLce6nCa+L5LYK1aBdb60BYbMeWk1qmG6Nk9OnYLhzDyrd9iHDd7X95OM6X5wiMVZRn5ebw4askTTc50xmrg4eic2U1w1JpSEjdH/u/hXrWKSMWAxaj34uQnMuWxPZEXoVxzGyuUbroXRfkhzpqmqqqOcypjsWPdq5BOUGL/Riwjm6yMI0x9kbO8+VoQ6RYfjAbxNriZ1cQ+AW1fqEgnRWXmjt4Z1M0ygUBi8w71bDML1YG6UHeC2cJ2CCCxSrfycKQhpSdI1QIuwd2eyIpd4LgwrMiY3xNWreAF+qobNxvE7ypKTISNrz0iYIhU0aKNlcGwYd0FXIRfKVBzSBe4MRK2pGLDNO6ytoHxvJweZ8h1XG8RWc4aB5gTnB7Tjiqym4b64lRdj1DPHJnzD4aqRixpXhzYzWVDN2kONCR5i2quYbnVFN4sSfLiKeOwKX4JdmzpYixNZXjLkG14seS6KR0Wl8Itp5IMIWFpnNokjRH76RYRZAcx0jP0V5/GfNNTi5QsEU98en0SiXHQGXnROiHpRUDXTl8FmJORjwXc0AjrEMuQ2FDJDmAIlKUSLhjbIiKw3iaqp5TVyXuz0ZMYBhnqhcwqULqtFSuIKpaW8FgF8QJfP2frADf4kKZG1bQ99MrRrb2A="}
        try:
            url = 'https://www.vavoo.tv/api/box/ping2'
            req = self.session.post(url, data=vec).json()
            return req['response'].get('signed')
        except Exception as e:
            return None

    def resolve_link(self, link, streammode=1, verbose=True):
        if not "vavoo" in link:
            return None

        if streammode == 1:
            signature = self.getAuthSignature()
            if not signature:
                return self.resolve_link(link, streammode=0, verbose=verbose)

            headers = {
                "user-agent": "MediaHubMX/2",
                "accept": "application/json",
                "content-type": "application/json; charset=utf-8",
                "content-length": "115",
                "accept-encoding": "gzip",
                "mediahubmx-signature": signature
            }
            data = {
                "language": "de",
                "region": "AT",
                "url": link,
                "clientVersion": "3.0.2"
            }

            try:
                resp = self.session.post("https://vavoo.to/mediahubmx-resolve.json", json=data, headers=headers, timeout=10)
                resp.raise_for_status()

                result = resp.json()
                if isinstance(result, list) and result and result[0].get("url"):
                    resolved_url = result[0]["url"]
                    channel_name = result[0].get("name", "Unknown")
                    return resolved_url
                elif isinstance(result, dict) and result.get("url"):
                    return result["url"]
                else:
                    return None

            except Exception as e:
                return None
        else:
            try:
                ts_signature = self.gettsSignature()
                if not ts_signature:
                    return None

                ts_url = "%s.ts?n=1&b=5&vavoo_auth=%s" % (link.replace("vavoo-iptv", "live2")[0:-12], ts_signature)
                return ts_url
            except Exception as e:
                return None

    def test_url(self, url):
        try:
            resp = self.session.head(url, timeout=5)
            return resp.status_code == 200
        except:
            return False

    def resolve_with_fallback(self, link, verbose=False):
        resolved = self.resolve_link(link, streammode=1, verbose=verbose)
        if resolved:
            return resolved, "principale"

        resolved = self.resolve_link(link, streammode=0, verbose=verbose)
        if resolved:
            return resolved, "fallback"

        return None, None

def vavooChPlay(parIn):
    video_urls = []
    resolver = VavooResolver()
    resolved, method = resolver.resolve_with_fallback(parIn)
    if resolved:
        logga("Link risolto con metodo: "+method)
        logga(resolved)
        video_urls.append((resolved, "[COLOR lime]PLAY VIDEO[/COLOR]", "PLAY VIDEO"))
    else:
        logga("Impossibile risolvere il link")
        video_urls.append(("ignore", "[COLOR red]NO LINK FOUND[/COLOR]", "PLAY VIDEO"))
    
    return video_urls

def filemoon(parIn):
    headers = {
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    s = requests.Session()
    page = s.get(parIn, headers=headers)
    link = re.findall('<iframe src="(.*?)" frameborder="0"',page.text)[0]
    return urlsolver(link)


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

def infoCode(parIn=''):
    logga('ParIn: '+parIn)
    video_urls = []
    launcher_vers="1.0.0"
    home = ''
    if PY3:
        home = xbmcvfs.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path'))
    else:
        home = xbmc.translatePath(xbmcaddon.Addon(id=addon_id).getAddonInfo('path').decode('utf-8'))
    launcher_file = os.path.join(home, 'launcher.py')
    if os.path.exists(launcher_file)==True:
        resF = open(launcher_file)
        resolver_content = resF.read()
        resF.close()
        launcher_vers = re.findall("versione='(.*)'",resolver_content)[0]
    mess="L_V: "+launcher_vers+" - R_V: "+versione
    msgBox(mess)
    return None


def ppv_to(parIn):
    import base64
    video_urls = []
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0'
    headers = {
        'user-agent': user_agent,
        'referer': "https://ppvs.to/"
    }
    s = requests.Session()
        
    response = s.get(parIn, headers=headers)
    logga ("PPV_PAGE ==> "+response.text)
    stream_url = re.findall('const src = atob\("(.*?)"\)', response.text)[0]
    stream_url = base64.b64decode(stream_url).decode("utf-8")
    logga ("URL IN ==> "+parIn)
    link=stream_url.replace("index.m3u8", "tracks-v1a1/mono.ts.m3u8|Referer=https://playembed.top/&Origin=https://playembed.top&User-Agent="+user_agent)
    
    jsonText='{"SetViewMode":"50","items":['
    jsonText = jsonText + '{"title":"[COLOR lime]PLAY STREAM [/COLOR] [COLOR gold](DIRECT)[/COLOR]","link":"'+link+'",'
    jsonText = jsonText + '"thumbnail":"https://i.imgur.com/8EL6mr3.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"},'
    jsonText = jsonText + '{"title":"[COLOR orange]PLAY STREAM [/COLOR] [COLOR gold](FFMPEG)[/COLOR]","myresolve":"ffmpeg_noRef@@'+link+'",'
    jsonText = jsonText + '"thumbnail":"https://i.imgur.com/8EL6mr3.png",'
    jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
    jsonText = jsonText + '"info":"by MandraKodi"}'
    
    jsonText = jsonText + "]}"
    
    video_urls.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))
    
    return video_urls



def resolve_link(url):
    import json, base64, time
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0'
    m3u8 = "IgnoreMe"
    logga ("URL IN ==> "+url)
    try:
        dadUrl="https://daddyhd.com/watch/stream-"+url+".php"
        #response = get(url)
        headers = {
            'user-agent': user_agent,
            'referer': "https://daddyhd.com/"
        }
        s = requests.Session()
        
        
        iframe_url = "https://epicplayplay.cfd/premiumtv/daddyhd.php?id="+url
        response = s.get(iframe_url, headers=headers)
        js = response.text
        logga ("SOURCE2 ==> "+js)
        params = {
            "channel_key": None,
            "auth_token": None,
            "auth_country": None,
            "auth_ts": None,
            "auth_expiry": None,
        }

        # intercetta QUALSIASI const var_<qualcosa> = "valore";
        pattern = r'const\s+var_[a-zA-Z0-9]+\s*=\s*["\']([^"\']+)["\']'

        matches = re.findall(pattern, js)

        if len(matches) >= 5:
            params["auth_token"]   = matches[0]
            params["channel_key"]  = matches[1]
            params["auth_country"] = matches[2]
            params["auth_ts"]      = matches[3]
            params["auth_expiry"]  = matches[4]

        logga("channel_key ==> " + str(params["channel_key"]))
        logga("auth_token ==> " + str(params["auth_token"]))
        logga("auth_country ==> " + str(params["auth_country"]))
        logga("auth_ts ==> " + str(params["auth_ts"]))
        logga("auth_expiry ==> " + str(params["auth_expiry"]))

        channel_key   = params["channel_key"]
        auth_token    = params["auth_token"]
        sess_split = auth_token.split(".")
        session_token = auth_token
        auth_country  = params["auth_country"]
        time_stamp    = params["auth_ts"]
        lang = 'it-IT'
        screen = '1920x1080'
        time_zone = "Europe/Rome"
        fingerprint = f"{user_agent}|{screen}|{time_zone}|{lang}"
        sign_data = f"{channel_key}|{auth_country}|{auth_token}|{user_agent}|{fingerprint}"
        logga("SIGN_DATA: "+str(sign_data.encode("utf-8")))
        client_token = base64.b64encode(sign_data.encode("utf-8")).decode("ascii")

        heartbeat= "https://chevy.kiko2.ru/heartbeat"
        
        referer="https://epicplayplay.cfd"
        heartbeat_headers = {
            'Accept': '*/*',
            "X-User-Agent": user_agent,
            "User-Agent": user_agent,
            "accept-encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,lt;q=0.5,de;q=0.4,fr;q=0.3,hu;q=0.2,ru;q=0.1,sv;q=0.1,da;q=0.1,ro;q=0.1,pl;q=0.1,hr;q=0.1",
            "Referer": referer,
            "Origin": referer,
            "Connection": "Keep-Alive",
            "Authorization": f"Bearer {session_token}",
            "X-Channel-Key": channel_key,
            "X-Client-Token": client_token,
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Opera";v="124"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Priority': 'u=1, i'
        }

        heart_resp = s.get(heartbeat, headers=heartbeat_headers, timeout=10)
        content_encoding = heart_resp.headers.get('Content-Encoding')
        logga("heart_resp ==> "+str(heart_resp.status_code)+" ("+content_encoding+")")

        server_lookup_url = f"https://chevy.giokko.ru/server_lookup?channel_id={channel_key}"
        lookup_headers = headers.copy()
        lookup_headers.update({
            'Accept': '*/*',
            'accept-encoding': 'gzip, deflate, zstd',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,lt;q=0.5,de;q=0.4,fr;q=0.3,hu;q=0.2,ru;q=0.1,sv;q=0.1,da;q=0.1,ro;q=0.1,pl;q=0.1,hr;q=0.1',
            'Origin': referer,
            'Referer': referer+"/",
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Opera";v="124"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Priority': 'u=1, i',
        })
        lookup_resp = s.get(server_lookup_url, headers=lookup_headers, timeout=6)
        content_encoding = lookup_resp.headers.get('Content-Encoding')
        logga("lookup_resp ==> "+str(lookup_resp.status_code)+" ("+content_encoding+")")
        server_key = find_single_match(lookup_resp.text, '{"server_key":"(.*?)"}')
        try:
            server_data = lookup_resp.json()
            server_key = server_data.get('server_key')
        except Exception:
            pass
        logga("server_key ==> "+server_key)
        if server_key == 'top1/cdn':
            stream_url = f'https://top1.kiko2.ru/top1/cdn/{channel_key}/mono.css'
        else:
            stream_url = f'https://{server_key}new.kiko2.ru/{server_key}/{channel_key}/mono.css'
        
        uaenc=myParse.quote(user_agent, safe='')
        cookie = "eplayer_session=" + session_token
        cookenc=myParse.quote(cookie, safe='')

        m3u8 = f'{stream_url}|Referer={referer}/&Origin={referer}&Connection=Keep-Alive&User-Agent={uaenc}&Cookie={cookenc}'
        m3u8_resp = s.get(m3u8)
        logga ("SOURCE_M3U8 ==> "+m3u8_resp.text)
        #m3u8 = f'{m3u8}|{urlencode(heartbeat_headers)}'
    except Exception as err:
        import traceback
        
        errMsg="ERROR_MK2: {0}".format(err)
        msgBox(errMsg)
        traceback.print_exc()
    
    return m3u8

def epgInfo(parIn, timeout=10):
    import json
    url="https://guidatv.org/canali/"+parIn
    req = Request(
        url,
        headers={
            "User-Agent": "Kodi/EPG-Addon",
            "Accept-Language": "it-IT,it;q=0.9"
        }
    )

    with urlopen(req, timeout=timeout) as r:
        html = r.read().decode("utf-8", errors="ignore")
    
    parser = EPGParser()
    parser.feed(html)

    epg = parser.data
    #logga("EPG: "+json.dumps(epg, indent=2, ensure_ascii=False))
    links = []
    jsonText='{"SetViewMode":"503","items":['
    numIt=0
    for p in epg["programmazione"]:
        orario = p["orario"]
        titolo = p["titolo"]
        desc = p["descrizione"]
        durata = p["durata"]
        img="https://img.pikbest.com/png-images/20250410/youtube-channel-logo-design-as-like-tv_11657892.png!sw800"
        if p["immagine_programma"]:
            img = p["immagine_programma"]

        
        if (numIt > 0):
            jsonText = jsonText + ','    
        jsonText = jsonText + '{"title":"[COLOR blue]'+orario+'[/COLOR] [COLOR gold]'+titolo.replace('"',"")+'[/COLOR] [COLOR lime]('+durata+')[/COLOR]",'
        jsonText = jsonText + '"myresolve":"showMsg@@Il link va cercato nelle liste disponibili",'
        jsonText = jsonText + '"thumbnail":"'+img+'",'
        jsonText = jsonText + '"fanart":"https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",'
        jsonText = jsonText + '"info":"'+desc.replace('"',"")+'"}'
        numIt=numIt+1
    
    
    jsonText = jsonText + "]}"
    logga('JSON-ANY: '+jsonText)
    links.append((jsonText, "PLAY VIDEO", "No info", "noThumb", "json"))

    return links

def extract_clean_text(html_fragment):
    parser = CleanTextParser()
    parser.feed(html_fragment)
    return parser.get_text()

class CleanTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.chunks = []

    def handle_data(self, data):
        self.chunks.append(data)

    def handle_comment(self, data):
        # ignora completamente i commenti <!-- -->
        pass

    def get_text(self):
        return ' '.join(
            ' '.join(self.chunks).split()
        )


def normalize_image_url(url):
    if not url:
        return None

    if "/_next/image" in url:
        match = re.search(r"url=([^&]+)", url)
        if match:
            return unquote(match.group(1))

    if url.startswith("//"):
        return "https:" + url

    return url

def parse_duration(text):
    text = text.lower()

    hours = 0
    minutes = 0

    m = re.search(r'(\d+)\s*ore?', text)
    if m:
        hours = int(m.group(1))

    m = re.search(r'(\d+)\s*min', text)
    if m:
        minutes = int(m.group(1))

    total_minutes = hours * 60 + minutes

    return total_minutes if total_minutes > 0 else None


class EPGParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.data = {
            "canale": "",
            "giorno": "",
            "subtitle_raw": "",
            "immagine_canale": None,
            "programmazione": []
        }

        self._current_program = None
        self._card_depth = 0
        self._last_hour = ""
        self._subtitle_buffer = ""

        self._in_channel_title = False
        self._in_program_title = False
        self._in_subtitle = False
        self._in_description = False
        self._in_day = False

    def handle_comment(self, data):
        pass

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
    
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        # Nome canale
        if tag == "h1" and "class" in attrs and "title" in attrs["class"]:
            self._in_channel_title = True

        # Giorno
        if tag == "button" and attrs.get("id") == "dayDropdownMenuButton":
            self._in_day = True

        # Orario
        if tag == "h3" and "class" in attrs and "hour" in attrs["class"]:
            self._last_hour = ""

        # Inizio card programma
        if tag == "div" and attrs.get("data-testid") == "channel-program-card":
            self._current_program = {
                "orario": "",
                "titolo": "",
                "durata": "",
                "categoria": "",
                "descrizione": "",
                "immagine_programma": None
            }
            self._card_depth = 1
            return

        # Profondita' card
        if self._current_program and tag == "div":
            self._card_depth += 1

        # Titolo programma
        if self._current_program and tag == "h2" and "class" in attrs and "card-title" in attrs["class"]:
            self._in_program_title = True

        # Sottotitolo
        if self._current_program and tag == "p" and "class" in attrs and "subtitle" in attrs["class"]:
            self._in_subtitle = True

        # Descrizione
        if self._current_program and tag == "p" and "class" in attrs and "program-description" in attrs["class"]:
            self._in_description = True

        # Immagine programma
        if self._current_program and tag == "img" and "class" in attrs and "card-img" in attrs["class"]:
            self._current_program["immagine_programma"] = normalize_image_url(attrs.get("src"))

        # Immagine canale
        if not self.data["immagine_canale"] and tag == "img" and "alt" in attrs:
            if "logo canale" in attrs["alt"].lower():
                self.data["immagine_canale"] = normalize_image_url(attrs.get("src"))

    def handle_endtag(self, tag):

        if self._current_program and tag == "div":
            self._card_depth -= 1

            if self._card_depth == 0:

                # PARSA DURATA PRIMA
                if self._subtitle_buffer:
                    durata_min = parse_duration(self._subtitle_buffer)
                    if durata_min:
                        self._current_program["durata"] = f"{durata_min} min"
                    self._subtitle_buffer = ""

                # NORMALIZZA TESTI
                if self._current_program["titolo"]:
                    self._current_program["titolo"] = " ".join(
                        self._current_program["titolo"].split()
                    )

                if self._current_program["descrizione"]:
                    self._current_program["descrizione"] = " ".join(
                        self._current_program["descrizione"].split()
                    )

                # SALVA PROGRAMMA
                if self._current_program["titolo"] and self._current_program["orario"]:
                    self.data["programmazione"].append(self._current_program)

                # RESET
                self._current_program = None

        # reset flag
        self._in_channel_title = False
        self._in_program_title = False
        self._in_subtitle = False
        self._in_description = False
        self._in_day = False


    def handle_data(self, data):
        text = data.strip()
        if not text:
            return

        # Orario
        if re.match(r"^\d{1,2}:\d{2}$", text):
            self._last_hour = text
            return

        # Giorno
        if self._in_day:
            self.data["giorno"] = text
            return

        # Nome canale
        if self._in_channel_title and not self.data["canale"]:
            self.data["canale"] = text.replace("Guida Tv", "").strip()
            return

        if not self._current_program:
            return

        # Assegna orario
        if not self._current_program["orario"] and self._last_hour:
            self._current_program["orario"] = self._last_hour

        # Titolo programma
        if self._in_program_title:
            self._current_program["titolo"] += text + " "
            return

        if self._in_subtitle:
            self._subtitle_buffer += text + " "
            return
        
        # Descrizione
        if self._in_description:
            self._current_program["descrizione"] += text

def showMsg(parIn):
    msgBox(parIn)

def sansat(parIn):
    import ast
    page="https://vividmosaica.com/embed3.php?player=desktop&live=do"+parIn
    head={
        "User-Agent":"Mozilla",
        "Referer":"https://sansat.link/",
        "Origin":"https://sansat.link"
    }
    s = requests.Session()
    response = s.get(page, headers=head)
    pattern = r"\(\s*(\[[^\]]+\])\.join\(\"\"\)"
    array_match = re.findall(pattern, response.text, re.DOTALL)
    chars = ast.literal_eval(array_match[0])
    url = "".join(chars)
    normalized = url.replace("\\/", "/")
    finalUrl=normalized.replace("https:////", "https://")
    logga ("SANSAT URL ==> "+finalUrl)
    video_urls = []
    video_urls.append((finalUrl+"|Referer=https://vividmosaica.com/&Origin=https://vividmosaica.com&User-Agent=Mozilla", "[COLOR lime]PLAY STREAM[/COLOR]"))
    return video_urls




class FedermotoAPI:
    BASE_URL = "https://api.federmoto.tv/api/v1/it"
    FANART = "https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg"

    def __init__(self, timeout=15):
        self.timeout = timeout
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Kodi-FedermotoTV"
        }

    def _get(self, url):
        r = requests.get(url, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ---------------------------------------------------
    # 1) SPORTS
    # ---------------------------------------------------
    def getSports(self):
        url = f"{self.BASE_URL}/sports"
        data = self._get(url)
        
        items = []
        for sport in data.get("data", []):
            items.append({
                "title": f"[COLOR lime]{sport.get('name')}[/COLOR]",
                "thumbnail": sport.get("thumb"),
                "fanart": self.FANART,
                "myresolve": f"mototv@@1__{sport.get('id')}"
            })

        return {
            "SetViewMode": "500",
            "items": items
        }

    # ---------------------------------------------------
    # 2) CATEGORIES BY SPORT
    # ---------------------------------------------------
    def getCategories(self, id_sport):
        url = f"{self.BASE_URL}/sport/{id_sport}/categories"
        data = self._get(url)

        items = []
        for cat in data.get("data", []):
            items.append({
                "title": f"[COLOR lime]{cat.get('name_category')}[/COLOR]",
                "thumbnail": cat.get("logo"),
                "fanart": self.FANART,
                "myresolve": f"mototv@@2__{id_sport}__{cat.get('id_category')}__0"
            })

        return {
            "SetViewMode": "500",
            "items": items
        }

    # ---------------------------------------------------
    # 3) CONTENT LIST
    # ---------------------------------------------------
    def getContentList(self, id_sport, id_category, offset=0):
        url = (
            f"{self.BASE_URL}/list?"
            f"sport={id_sport}&category={id_category}"
            f"&offset={offset}&status=finished&order=date.desc"
        )

        data = self._get(url)

        items = []
        widgets = data.get("data", {}).get("widgets", [])
        for widget in widgets:
            for content in widget.get("items", []):
                items.append({
                    "title": f"[COLOR lime]{content.get('title')}[/COLOR]",
                    "thumbnail": content.get("image"),
                    "fanart": self.FANART,
                    "myresolve": f"mototv@@3__{content.get('id')}"
                })
        
        # -----------------------------
        # PAGINAZIONE (NEXT PAGE)
        # -----------------------------
        has_next = data.get("data", {}).get("continue", False)

        if has_next:
            next_offset = str(int(offset) + len(items))

            items.append({
                "title": "[COLOR yellow]>> Pagina successiva[/COLOR]",
                "thumbnail": "",
                "fanart": self.FANART,
                "myresolve": (
                    f"mototv@@2__{id_sport}"
                    f"__{id_category}"
                    f"__{next_offset}"
                )
            })

        return {
            "SetViewMode": "50",
            "items": items
        }

    # ---------------------------------------------------
    # 4) CONTENT DETAIL (HLS)
    # ---------------------------------------------------
    def getContent(self, id_content):
        url = f"{self.BASE_URL}/content/{id_content}"

        try:
            data = self._get(url)
        except Exception:
            return {
                "items": [{
                    "title": "[COLOR red]Errore di rete[/COLOR]",
                    "thumbnail": "",
                    "fanart": self.FANART,
                    "link": ""
                }]
            }

        # -----------------------------
        # ACCESS DENIED / NOT FREE
        # -----------------------------
        if not data.get("success") or not data.get("data") or data.get("success")==False:
            error_msg = "Contenuto non disponibile"

            errors = data.get("errors", [])
            if errors:
                error_msg = errors[0].get("message", error_msg)

            return {
                "items": [{
                    "title": f"[COLOR red]{error_msg}[/COLOR]",
                    "thumbnail": "",
                    "fanart": self.FANART,
                    "link": ""
                }]
            }

        # -----------------------------
        # CONTENT OK
        # -----------------------------
        content = data["data"]
        videos = content.get("videos", [])

        hls = None
        if videos:
            hls = videos[0].get("hls")

        return {
            "SetViewMode": "50",
            "items": [{
                "title": f"[COLOR lime]{content.get('title')}[/COLOR]",
                "thumbnail": content.get("preview_img"),
                "fanart": self.FANART,
                "link": hls
            }]
        }

def mototv(parIn):
    import json
    mode=0
    arrPar=parIn.split("__")
    mode=arrPar[0]
    logga("MODE ==> "+mode)
    api = FedermotoAPI()
    ret=""
    if mode == "0":
        ret=json.dumps(api.getSports())
    if mode == "1":
        par1=arrPar[1]
        ret=json.dumps(api.getCategories(par1))
    if mode == "2":
        par1=arrPar[1]
        par2=arrPar[2]
        par3=arrPar[3]
        ret=json.dumps(api.getContentList(par1, par2, par3))
    if mode == "3":
        par1=arrPar[1]
        ret=json.dumps(api.getContent(par1))
    
    
    logga("SPORT ==> "+ret)
    video_urls= []
    video_urls.append((ret, "PLAY VIDEO", "No info", "noThumb", "json"))
    return video_urls    

def run (action, params=None):
    logga('Run version '+versione)
    commands = {
        'myStream': myStream,
        'wizhd': wizhd,
        'daddy': daddy,
        'antena': antena,
        'wigi': wigi,
        'proData': proData,
        'risolvi': urlsolver,
        'dplay': dplay,
        'dplayLive': dplayLive,
        'disco': discovery,
        'skyTV': skyTV,
        'mac': macLink,
        'scws': getUrlSc,
        'scws2': scwsNew,
        'moviesc': scws,
        'seriesc': getScSerie,
        'assia': assia,
        'vudeo': vudeo,
        'pulive': pulive,
        'voe': voe,
        'supVid': supervideo,
        'taxi': taxi,
        'scom': scommunity,
        'stape': streamTape,
        'urlsolve': resolveMyUrl,
        'rocktalk': rocktalk,
        'lvtv': livetv,
        'toonita' : toonIta,
        'uprot' : uprot,
        'stsb' : streamsb,
        'imdb' : imdb,
        'bing' : bing,
        'cb01' : cb01,
        'platin' : platin,
        'webcam' : webcam,
        'markky' : markky,
        'pepper':pepper,
        'wiki':wikisport,
        'daily':daily,
        'anyplay':anyplay,
        'enigma4k':enigma4k,
        'testDns':testDns,
        'nopayMenu':nopayMenu,
        'menuIstorm':menuIstorm,
        'daddyCode':daddyCode,
        'antenaCode':antenaCode,
        'infoCode':infoCode,
        'imdbList':imdbList,
        'frame':getSourceFrame,
        'sib':sibNet,
        'hunter':hunterjs,
        'nflinsider':nflinsider,
        'ffmpeg':ffmpeg,
        'ffmpeg_noRef':ffmpeg_noRef,
        'koolto':koolto,
        'spon':sportOnline,
        'mixdrop':mixdrop,
        'filemoon':filemoon,
        'sportMenu': createSportMenu,
        'vavooCh':vavooChList,
        'vavooPlay':vavooChPlay,
        'tmdb':get_tmdb_video,
        'tmdbs':get_tmdb_episode_video,
        'gdplayer':gdplayer,
        'freeshot':freeshot,
        'tvapp':tvapp,
        'ppv':ppv_to,
        'm3uPlus':m3uPlus,
        'gaga':gaga,
        'epg':epgInfo,
        'sansat':sansat,
        "mototv":mototv,
        'showMsg':showMsg
    }

    if action in commands:
        return commands[action](params)
    else:
        raise ValueError('Invalid command: {0}!'.action)
