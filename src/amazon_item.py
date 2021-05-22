import random
import time
from collections import deque
from enum import Enum
from threading import Lock
from threading import Event
from threading import Timer
from threading import Thread
import threading
import traceback
import re
from src.proxy import Proxy
from src.net_tools import *
from src.net_tools_exceptions import *


class ItemStatus(Enum):
    UNTRACKED = 1
    UNAVAILABLE = 2
    AVAILABLE = 3
    PROCESSING = 4
    ERROR = 5


class AmazonItem():
    """
    Define an item will be tracked
    """

    proxies = [Proxy()]
    smart_sleep_enabled = False
    smart_sleep_min_timer = 0
    smart_sleep_max_timer = 0
    smart_sleep_min_time = 0
    smart_sleep_max_time = 0
    get_stats_callback = None
    max_workers_count = 7

    def __init__(
            self,
            name,
            url,
            check_interval=2000,
            logger=None,
            raw_status_changed_callback=None,
            status_changed_callback=None,
            stats_sample_count=100):
        self.name = name
        self.url = url
        self.check_interval = check_interval
        self.status_changed_callback = status_changed_callback
        self.raw_status_changed_callback = raw_status_changed_callback
        self.logger = logger
        self.stats_sample_count = stats_sample_count

        self.stats = deque(maxlen=self.stats_sample_count)
        self._workers_statuses = [False] * AmazonItem.max_workers_count
        self.errors_counter = 0
        self._status = None
        self._status_changed_lock = Lock()
        self.status = ItemStatus.UNTRACKED

        # antibot smart sleep function
        self._smart_sleep_timeoff = Event()
        self._smart_sleep_timer = None

    def get_status(self):
        return self._status

    def set_status(self, value):
        if value == ItemStatus.ERROR:
            self.errors_counter += 1
        else:
            self.errors_counter = 0
        # raw_status_changed_callback called always
        if self.raw_status_changed_callback:
            self.raw_status_changed_callback(self)

        if self._status == value:
            return
        if self._status == ItemStatus.PROCESSING and \
                value == ItemStatus.AVAILABLE:
            # it's for multiply threads
            return

        with self._status_changed_lock:
            self._status = value

        # status_changed_callback called only when status changed
        if self.status_changed_callback:
            self.status_changed_callback(self)

    status = property(get_status, set_status)

    @staticmethod
    def init_proxies(proxy_dicts_list):
        AmazonItem.proxies = []
        for proxy_dict in proxy_dicts_list:
            p = Proxy(proxy_dict['name'],
                      proxy_dict['ip_address'],
                      proxy_dict['port'],
                      proxy_dict['auth_user'],
                      proxy_dict['auth_pass'])
            AmazonItem.proxies.append(p)

    @staticmethod
    def init_smart_sleep(
            smart_sleep_min_timer=60 * 15,
            smart_sleep_max_timer=60 * 30,
            smart_sleep_min_time=5000,
            smart_sleep_max_time=10000):
        AmazonItem.smart_sleep_enabled = True
        AmazonItem.smart_sleep_min_timer = smart_sleep_min_timer
        AmazonItem.smart_sleep_max_timer = smart_sleep_max_timer
        AmazonItem.smart_sleep_min_time = smart_sleep_min_time
        AmazonItem.smart_sleep_max_time = smart_sleep_max_time

    @staticmethod
    def set_get_stats_callback(callback):
        AmazonItem.get_stats_callback = callback

    def smart_sleep_start_timer(self):
        smart_sleep_timer = random.randrange(
            AmazonItem.smart_sleep_min_timer,
            AmazonItem.smart_sleep_max_timer
        )
        self._smart_sleep_timer = Timer(
            smart_sleep_timer,
            lambda: self._smart_sleep_timeoff.set())
        self._smart_sleep_timer.setName(self.name + '_SmartSleepTimer')
        self._smart_sleep_timer.start()

    def try_check_availability(self):
        available = None
        try:
            available, context = NetTools.check_availability(
                self.url,
                AmazonItem.proxies)
        except Exception as ex:
            # tb = ''.join(
            #      traceback.TracebackException.from_exception(ex).format())
            # print(tb)
            self.status = ItemStatus.ERROR
            raise ex

        self._add_stat(context['duration'])
        if available:
            self.status = ItemStatus.AVAILABLE
        else:
            self.status = ItemStatus.UNAVAILABLE

    def _add_stat(self, duration):
        self.stats.append(duration)
        if len(self.stats) == self.stats_sample_count \
                and AmazonItem.get_stats_callback is not None:
            AmazonItem.get_stats_callback(self)

    def _check_availability(self,
                            bad_response_exception_callback=None,
                            parse_page_exception_callback=None,
                            other_exception_callback=None):
        try:
            self.try_check_availability()
        except BadResponseException as ex:
            self._add_stat(ex.context['duration'])
            if bad_response_exception_callback:
                bad_response_exception_callback(ex.status_code, ex.context)
        except ParsePageException as ex:
            self._add_stat(ex.context['duration'])
            if parse_page_exception_callback:
                parse_page_exception_callback(ex.http_body, ex.context)
        except CurlException as ex:
            # tb = ''.join(
            #      traceback.TracebackException.from_exception(ex).format())
            # print(tb)
            # When something wrong we need clear smart sleep timer
            # if AmazonItem.smart_sleep_enabled:
            #     self._smart_sleep_timer.cancel()
            #     self._smart_sleep_timer = None
            #     self._smart_sleep_timeoff.clear()
            if other_exception_callback:
                other_exception_callback(ex)
        thread_name = threading.current_thread().name
        i_str = re.split(r'worker ', thread_name)
        i = int(i_str[1])
        self._workers_statuses[i] = False

    def track(self,
              bad_response_exception_callback=None,
              parse_page_exception_callback=None,
              other_exception_callback=None):
        start_delay = random.randrange(300, 2000)
        time.sleep(start_delay / 1000)

        if AmazonItem.smart_sleep_enabled:
            self.smart_sleep_start_timer()

        # Track until processing will start.
        # (!) After processing you need restart tracking item.
        while self.status != ItemStatus.PROCESSING:
            worker_i = (self._workers_statuses + [False]).index(False)
            if worker_i != AmazonItem.max_workers_count:
                worker = Thread(
                    target=self._check_availability,
                    args=(bad_response_exception_callback,
                          parse_page_exception_callback,
                          other_exception_callback),
                    daemon=True)
                self._workers_statuses[worker_i] = True
                worker.name = ' '.join((self.name,
                                        'worker',
                                        str(worker_i)))
                worker.start()

            time_fuziness = random.randrange(20, 50)
            time.sleep((self.check_interval + time_fuziness) / 1000)

            if AmazonItem.smart_sleep_enabled and \
                    self._smart_sleep_timeoff.is_set():
                smart_sleep_time = random.randrange(
                    AmazonItem.smart_sleep_min_time,
                    AmazonItem.smart_sleep_max_time
                )
                time.sleep(smart_sleep_time / 1000)
                self._smart_sleep_timeoff.clear()
                self.smart_sleep_start_timer()

        # When we are in item processing clear smart sleep timer
        if AmazonItem.smart_sleep_enabled:
            self._smart_sleep_timer.cancel()
            self._smart_sleep_timer = None
            self._smart_sleep_timeoff.clear()
