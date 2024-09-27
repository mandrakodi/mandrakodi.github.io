versione='1.1.1'
from datetime import datetime

import requests, logging
import math
import re

try:
    from urllib.parse import quote as quoter
    from urllib.parse import unquote as unquoter
    from urllib.parse import urlparse, urlsplit
    from urllib.parse import parse_qs

except ImportError:
    from urllib import quote as quoter
    from urllib import unquote as unquoter


class PortalApi:

    def __init__(self, url, mac=None, **kwargs):

        self.params = []

        if not mac:
            match = re.compile(r'(.*?)\?(.*?)($|(&.*?$))', re.MULTILINE).findall(url)[0]
            url = match[0]
            mac = match[1]
            try:
                self.params = re.compile(r'([^&?]*?)=([^&?]*)').findall(match[2])
            except:
                pass

        # ([^&?]*?)=([^&?]*)
        self.url = url
        self.mac = mac
        self.api_url = self.url + "/portal.php?"
        self.__dict__.update(**kwargs)
        self.token = ""
        self.request_headers = None
        self.types = ["Live", "VOD", "All"]

    def root(self):
        ret = []
        for st in self.types:
            ret.append((st, self.url + "?" + self.mac))
        return ret

    def set_headers(self):
        ua = 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: ' \
             '250 Safari/533.3 '
        self.request_headers = {
            'User-Agent': ua,
            'X-User-Agent': 'Model: MAG250; Link: WiFi',
            'Connection': 'keep-Alive',
            'Cookie': 'mac=' + quoter(self.mac) + "; stb_lang=en; timezone=Europe%2Amsterdam;",
            'Pragma': 'no-cache',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept-Encoding': 'gzip'
        }
        if self.token != "":
            self.request_headers['Authorization'] = 'Bearer ' + self.token

    def get_token(self):
        # req = requests.get(self.api_url + "type=stb&action=handshake&token=", headers=self.request_headers)
        res = self.do_request("type=stb&action=handshake")
        token = res["token"]
        self.token = token
        self.get_profile()

    def get_profile(self):
        # self.request_headers['Authorization'] = 'Bearer ' + self.token
        dt = datetime.now()
        timestamp = datetime.timestamp(dt)
        p = 'type=stb&action=get_profile&hd=1&ver=ImageDescription: 0.2.18-r23-254; ImageDate: Wed Oct 31 15:22:54 ' \
            'EEST 2018; PORTAL version: 5.5.0; API Version: JS API version: 343; STB API version: 146; Player Engine ' \
            'version: 0x58c&num_banks=2&sn=17F88C9910EF5&client_type=STB&image_version=218&video_out=hdmi&device_id' \
            '=F48C7788EF17D24F661C5A1782DF0D2237D545BE12A5A4B4325D89A52A7DF186&device_id2' \
            '=F48C7788EF17D24F661C5A1782DF0D2237D545BE12A5A4B4325D89A52A7DF186&signature' \
            '=845519FCE3386C1847AD3469AAD6D2773080C6F94CB59CD0A9E82605FAEDE02F&auth_second_step=1&hw_version=2.6-IB' \
            '-00&not_valid_token=0&metrics={"mac":"' + \
            self.mac + '","sn":"17F88C9910EF5","type":"STB",' \
                       '"model":"MAG254",' \
                       '"uid":"F48C7788EF17D24F661C5A1782DF0D2237D545BE12A5A4B4325D89A52A7DF186",' \
                       '"random":""}&hw_version_2=aff4d6ab1ab4e0660f09f89809c6e9782fa43263&timestamp=' \
            + str(timestamp) + '&api_signature=262 '
        self.do_request(p)
        res = self.do_request("type=stb&action=get_profile")
        # print(res)
        return res

    def get_categories(self, ltype="live"):
        self.get_token()
        url = "type=itv&action=get_genres" if ltype == "live" else "type=vod&action=get_categories"
        res = self.do_request(url, True)
        # print(res)
        if res:
            ret = []
            for gen in res:
                if "all" == gen["title"].encode('utf-8', errors='ignore').lower().decode():
                    continue
                ret.append(
                    (gen["id"], gen["title"].encode('utf-8', errors='ignore').decode(), self.url + "?" + self.mac))

            # print(ret)
            return ret

    def get_itv_genres(self):
        # self.request_headers['Authorization'] = 'Bearer ' + self.token
        return self.get_categories()

    def get_vod_genres(self):
        # self.request_headers['Authorization'] = 'Bearer ' + self.token
        return self.get_categories("vod")

    def get_genres(self):
        self.get_token()
        res = self.do_request("type=itv&action=get_genres", True)
        # print(res)

        ret = {}
        for g in res:
            ret[g["id"]] = {"title": g["title"], "alias": g["alias"]}

        return ret

    def get_all_channels(self):
        # self.request_headers['Authorization'] = 'Bearer ' + self.token
        self.get_token()
        # self.get_profile()
        res = self.do_request("type=itv&action=get_all_channels")
        # print(res)
        genres = self.get_genres()

        ret = []

        for i in res["data"]:
            id = i["id"]
            number = i["number"]
            name = i["name"]
            cmd = i['cmd']
            logo = i["logo"]
            tmp = i["use_http_tmp_link"]
            genre_id = i["tv_genre_id"]
            try:
                genre_title = genres[genre_id]['title']
            except:
                genre_title = ""

            try:
                cmd = cmd.split(" ")[1]
            except:
                pass

            ret.append((id, number, name, cmd, logo, tmp, genre_title))
        return ret

    def get_ordered_list(self, id_genre, ltype="live", check=False):
        self.get_token()
        if ltype == "live":
            url = "type=itv&action=get_ordered_list&genre=" + str(id_genre)
        else:
            url = "type=vod&action=get_ordered_list&genre=" + str(id_genre)
        url += "&force_ch_link_check=&fav=0&sortby=number&hd=0"

        tot_pages = 0
        page = 1

        ret = []

        while True:
            res = self.do_request(url + "&p=" + str(page), True)
            # print(res)
            if res and "data" in res:

                for ch in res["data"]:
                    # strm_url = ch["cmd"].replace("ffmpeg", "").strip()

                    ret.append((ch["name"], ch["cmd"]))

            if tot_pages == 0:
                tot_pages = math.ceil(int(res["total_items"]) / int(res["max_page_items"]))

            page += 1

            if page > tot_pages or check:
                break

        # print(ret)
        return ret

    def get_itv_list(self, id_genre):
        return self.get_ordered_list(id_genre)

    def get_vod_list(self, id_categ):
        return self.get_ordered_list(id_categ, "vod")

    def get_link(self, cmd, ltype="itv"):
        self.get_token()

        url = "type=" + ltype + "&action=create_link&cmd=" + cmd
        url += "&series=0&forced_storage=false&disable_ad=false&download=false&force_ch_link_check=false"

        res = self.do_request(url, True)
        if res:
            if res["id"].isdigit():
                link = res["cmd"]
            else:
                try:
                    strm_id = re.compile(r".*?/([\d]+(?:\.ts|$))").findall(res["id"])[0]
                    base = re.compile(r"(http.*?://.*?:[\d]+(?:/live/|/).*?/.*?/).*?(\?.*?)$").findall(res["cmd"])[0]
                    link = base[0] + strm_id + base[1]

                except Exception as e:
                    link = cmd
        else:
            link = cmd

        try:
            link = link.split(" ")[1]
        except:
            pass

        # link = re.sub(r"(http.*?//.*?:[\d]+)", self.url, link, 0, re.MULTILINE)
        params = ""
        if self.params:
            for par in self.params:
                params += "=".join(par) + "&"

        params = params.strip("&")

        if "User-Agent" not in params:
            params += "!User-Agent=Lavf53.32.100"
        if "Icy-MetaData" not in params:
            params += "&Icy-MetaData=1"

        return link + "|" + params

    def do_request(self, url, is_get=False):
        self.set_headers()
        request_url = self.api_url + url + "&JsHttpRequest=1-xml"

        parsed_url = urlparse(request_url)
        payload = parse_qs(parsed_url.query)
        # print(payload)
        try:
            if is_get:
                res = requests.get(self.api_url, headers=self.request_headers, params=payload, timeout=1)
            else:
                res = requests.post(self.api_url, headers=self.request_headers, data=payload, timeout=1)
            # print(res.text)

            if res.status_code > 399:
                return None
        except Exception as e:
            print(e)
            return None
        logging.warning("MANDRA_PORTAL: "+res.text)

        try:
            if "AVVISO" in res.text and "680/13/CONS" in res.text:
                import xbmcgui
                dialog = xbmcgui.Dialog()
                mess="La lista e' stata bloccata dalla magistratura.[CR]Prova ad usare una VPN"
                dialog.ok("MandraKodi", mess)
                return None
        except Exception:
            pass
        jres = res.json()

        if "js" in jres:
            return jres["js"]
        else:
            return None
