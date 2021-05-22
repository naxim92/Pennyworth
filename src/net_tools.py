import string
import random
import time
from random import choice
from io import BytesIO
import pycurl
import certifi
from bs4 import BeautifulSoup
from src.proxy import Proxy
from src.net_tools_exceptions import *


class NetTools():
    curl_languages = [
        'Accept-Language: en-US;q=0.9, ru;q=0.8, de;q=0.7, *;q=0.5',
        'Accept-Language: en-US;q=0.8, fr-CA;q=0.6, de;q=0.6, *;q=0.4',
        'Accept-Language: en-US;q=0.9, de;q=0.6, *;q=0.4',
        'Accept-Language: en-US, en;q=0.9, ru;q=0.6, *;q=0.4',
        'Accept-Language: en-US, de;q=0.7',
        'Accept-Language: en-US, fr;q=0.8, *;q=0.4',
        'Accept-Language: en-US, de;q=0.6, fr;q=0.3 *;q=0.4',
        'Accept-Language: en-US, de;q=0.7, *;q=0.3',
        'Accept-Language: en-US, en-GB;q=0.8, en;q=0.7',
        'Accept-Language: en-US, en-gb;q=0.7, de;q=0.3',
        'Accept-Language: en-US, en-gb;q=0.6, ru_UA;q=0.3',
        'Accept-Language: en-US, fr-CA;q=0,4',
        '']

    curl_static_user_agent = [
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safar3'
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) lio',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; ',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) l',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; TriGecko',
        'Mozilla/5.0 (Windows NT 6.1; Wrv:11.0) like Gecko',
        'Mozilla/5.0 (Windows N Gecko']

    @staticmethod
    def get_http(
            url,
            rand_user_agent=True,
            proxy=Proxy()):
        b_obj = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(curl.URL, url)
        curl.setopt(pycurl.CAINFO, certifi.where())
        curl.setopt(curl.WRITEFUNCTION, b_obj.write)
        # curl.setopt(pycurl.HEADERFUNCTION, parse_header)

        context = NetTools._get_context(rand_user_agent)
        # Parametrize curl request
        curl.setopt(curl.HTTPHEADER, context['headers'])
        curl.setopt(pycurl.USERAGENT, context['useragent'])
        curl.setopt(curl.ENCODING, context['encoding'])
        curl.setopt(pycurl.TIMEOUT, 20)
        curl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_0)
        # If we use a proxy
        if proxy.is_bypass is False:
            curl.setopt(pycurl.PROXY, proxy.ip_address)
            curl.setopt(pycurl.PROXYPORT, proxy.port)
            curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
            if proxy.auth_user is not None and proxy.auth_pass is not None:
                curl.setopt(
                    pycurl.PROXYUSERPWD,
                    ':'.join((proxy.auth_user, proxy.auth_pass)))
        # Whether we use proxy or not we need fill context for statistic
        context['proxy'] = proxy.name

        # Finish curl request
        timer_1 = time.perf_counter()
        try:
            curl.perform()
        except Exception as ex:
            raise CurlException(context, ex)
        timer_2 = time.perf_counter()
        context['duration'] = timer_2 - timer_1
        status_code = curl.getinfo(pycurl.HTTP_CODE)
        curl.close()
        response = b_obj.getvalue().decode()
        # print(str(status_code))
        # if 'MEOW' in response:
        #     print('MEOW')
        # else:
        #     print('BUN')
        return status_code, response, context

    @staticmethod
    def _get_context(rand_user_agent):
        context = {}
        headers = ['Accept-Charset: UTF-8']
        if choice([True, False]):
            headers.append(choice(NetTools.curl_languages))
        context['headers'] = headers
        if rand_user_agent:
            user_agent = NetTools._get_random_string()
        else:
            user_agent = choice(NetTools.curl_user_agent)
        context['useragent'] = user_agent
        context['ciphers'] = []
        context['encoding'] = 'gzip'
        return context

    @staticmethod
    def _get_random_string():
        string_length = random.randrange(5, 40)
        random_string = ''.join((random.choices(
            string.ascii_letters + string.digits + string.punctuation,
            k=string_length)))
        return random_string

    @staticmethod
    def _check_correct_page(bs):
        if bs.find(id='productTitle') is None and \
                bs.find(id='title') is None:
            return False
        else:
            return True

    @staticmethod
    def _check_availability_on_page(bs):
        if bs.find(id='buy-now-button') is None:
            return False
        else:
            return True

    # True - item is available for buying
    # False - item is unavailable
    @staticmethod
    def check_availability(url, proxies_list=[Proxy()]):
        random_proxy = random.choice(proxies_list)
        status_code, http_body, context = NetTools.get_http(
            url,
            proxy=random_proxy)
        if status_code >= 400:
            raise BadResponseException(status_code, context)
        soup = BeautifulSoup(http_body, 'html5lib')

        if not NetTools._check_correct_page(soup):
            raise ParsePageException(
                'There is no html tag with id productTitle or id title',
                http_body=http_body,
                context=context)

        if NetTools._check_availability_on_page(soup):
            return True, context
        else:
            return False, context
