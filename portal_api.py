import requests
import math

try:
    from urllib.parse import quote as quoter
    from urllib.parse import unquote as unquoter
except ImportError:
    from urllib import quote as quoter
    from urllib import unquote as unquoter


class PortalApi:

    def __init__(self, url, mac=None, **kwargs):

        if not mac:
            url, mac = url.split("?")

        self.url = url
        self.mac = mac
        self.api_url = self.url + "portal.php?"
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
        res = self.do_request("type=stb&action=get_profile")
        # print(res)
        return res

    def get_categories(self, ltype="live"):
        self.get_token()
        url = "type=itv&action=get_genres" if ltype == "live" else "type=vod&action=get_categories"
        res = self.do_request(url)
        # print(res)
        if res:
            ret = []
            for gen in res:
                if "all" == gen["title"].encode('utf-8', errors='ignore').lower().decode():
                    continue
                ret.append((gen["id"], gen["title"].encode('utf-8', errors='ignore').decode(), self.url + "?" + self.mac))

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
        res = self.do_request("type=itv&action=get_genres")
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
            res = self.do_request(url + "&p=" + str(page))
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

        "type=itv&action=create_link&cmd=ffmpeg%20http://localhost/ch/1823_&series=&forced_storage=0&disable_ad=0&download=0&force_ch_link_check=0&JsHttpRequest=1-xml"

        url = "type=" + ltype + "&action=create_link&cmd=" + cmd
        url += "&forced_storage=undefined&disable_ad=0&download=0"
        
        res = self.do_request(url)
        link = res["cmd"]
        try:
            link = link.split(" ")[1]
        except:
            pass

        return link

    def do_request(self, url):
        self.set_headers()
        url = self.api_url + url + "&JsHttpRequest=1-xml"
        res = requests.get(url, headers=self.request_headers, timeout=1)

        # print(res.text)
        jres = res.json()
        if "js" in jres:
            return jres["js"]
        else:
            return None
