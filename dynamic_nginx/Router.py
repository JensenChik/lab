# coding=utf-8

import requests, json
from IPy import IP


class Router:
    def __init__(self, model=None, login_name=None, passwd=None):
        self.model = model
        self.router = eval(model)(login_name, passwd)

    def get_ip(self):
        return self.router.get_ip()

    def reconnect(self):
        return self.router.reconnect()

    def is_private_ip(self):
        return IP(self.get_ip()).iptype() == 'PRIVATE'


class TPLINK_WR842N:
    def __init__(self, login_name=None, passwd=None):
        token_params = {"method": "do", "login": {"password": passwd}}  # 具体加密不清楚，直接copy浏览器
        index = "http://192.168.1.1/"
        token = json.loads(self.get_data(index, token_params)).get("stok")
        self.req_url = "http://192.168.1.1/stok=%s/ds" % token

    @staticmethod
    def get_data(url, data):
        return requests.post(url, data=json.dumps(data).encode('utf8')).text.decode()

    def get_ip(self):
        req_params = {"protocol": {"name": ["pppoe", "wan"]}, "network": {"name": "wan_status"}, "method": "get"}
        return json.loads(self.get_data(self.req_url, req_params)).get("network").get("wan_status").get("ipaddr")

    def reconnect(self):
        return self.disconnect()

    def disconnect(self):
        req_params = {"network": {"change_wan_status": {"proto": "pppoe", "operate": "disconnect"}}, "method": "do"}
        return json.loads(self.get_data(self.req_url, req_params))
