import os
import sys
from threading import Event
from threading import Thread
import logging
import traceback
import atexit
import random
import time
from src.config_entries import *
from src.config import *
from src.config_loader import *
from src.selenium_wrapper import *
from src.amazon_item import *
from src.localization_factory import LocalizationFactory
from src.notifyers import *
from src.tui import *


class Pennyworth():
    """
    Alfred Pennyworth helps you to buy on Amazon.
    Give config file path and go.
    Default config file config.yml.
    """

    script_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..')
    deps_dir = os.path.join(script_path, 'deps')
    log_dir = os.path.join(script_path, 'logs')
    tech_logfile_name = 'app.log'
    statistic_logfile_name = 'statistic.log'
    http_logfile_name = 'http_debug.log'
    sound_dir = script_path
    alarm_file_name = 'alarm.mp3'
    item_bad_checks_count = [5, 20, 100, 500, 1000]

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = None
        self.browser_instance = None
        self.ready_to_process_item = Event()
        self.ready_to_track = Event()
        self.keep_working_answer = Event()
        self.ui = None
        self.traking_items = []
        self.origin_stderr = None
        self.tech_logger = logging.getLogger('Tech')
        self.file_statistic_logger = None
        self.file_http_logger = None
        self.localization = None
        self.alarm = None
        self.telegram_bot = None

    def _get_config(self):
        """
        Read config to a dictionary
        """
        loader = ConfigLoader(self.config_path)
        config = loader.get_config()
        self.config = config

    def _generate_items_list(self):
        for i in self.config['amazon.items']:
            item = AmazonItem(
                name=i['name'],
                url=i['url'],
                check_interval=i['check_interval'],
                logger=None,
                raw_status_changed_callback=self._item_status_got_callback,
                status_changed_callback=self._item_status_changed_callback)
            self.traking_items.append(item)
        AmazonItem.init_proxies(self.config['antibot.proxies'])

    def _init_loggers(self):
        """
        Initiate loggers.
        tech_logger - errors and unhandled exceptions, perhaps stderror
        item_logger - item news during the checking and buying process,
                      for each item different logger
        statistic_logger - time, item_name, proxy_name, http_code,
                           perhaps bunned or correct pagee
        http_logger - http pages with bad parsing results
        """

        # Remember original stderr
        self.origin_stderr = sys.stderr
        app_log_file = open(os.path.join(
            Pennyworth.log_dir, Pennyworth.tech_logfile_name), 'a')
        sys.stderr = app_log_file

        # Configure tech_logger
        console_tech_handler = logging.StreamHandler()
        console_tech_format = logging.Formatter(
            fmt='%(asctime)s - [%(threadName)s] %(levelname)s - %(message)s',
            datefmt='%d-%m-%Y %H:%M:%S')
        console_tech_handler.setFormatter(console_tech_format)
        self.tech_logger.addHandler(console_tech_handler)
        console_tech_level = logging.getLevelName(self.config[
            'general.logs.level'])
        self.tech_logger.setLevel(console_tech_level)

        # Configure statistic_logger
        if self.config['general.logs.statistic']:
            self.file_statistic_logger = logging.getLogger('Statistic')
            file_statistic_handler = logging.FileHandler(os.path.join(
                Pennyworth.log_dir, Pennyworth.statistic_logfile_name))
            file_statistic_handler.setLevel(logging.INFO)
            file_statistic_format = logging.Formatter(
                fmt='%(asctime)s [%(threadName)s] %(message)s',
                datefmt='%d-%m-%Y %H:%M:%S')
            file_statistic_handler.setFormatter(file_statistic_format)
            self.file_statistic_logger.addHandler(file_statistic_handler)

        # Configure http_logger
        if self.config['general.logs.http_debug']:
            self.file_http_logger = logging.getLogger('HTTP')
            file_http_handler = logging.FileHandler(os.path.join(
                Pennyworth.log_dir, Pennyworth.http_logfile_name),
                'a',
                'utf-8')
            file_http_handler.setLevel(logging.INFO)
            file_http_format = logging.Formatter(
                fmt='%(asctime)s [%(threadName)s] %(message)s',
                datefmt='%d-%m-%Y %H:%M:%S')
            file_http_handler.setFormatter(file_http_format)
            self.file_http_logger.addHandler(file_http_handler)

        # Configure items' logger
        # INFO - UNAVAILABLE
        # WARNING - AVAILABLE
        # ERROR - ERROR
        # CRITICAL - PROCESSING
        for item in self.traking_items:
            logger = logging.getLogger(item.name)
            file_item_handler = logging.FileHandler(os.path.join(
                Pennyworth.log_dir, ''.join((item.name, '.log'))))
            file_item_handler.setLevel(logging.INFO)
            file_item_format = logging.Formatter(
                fmt='%(asctime)s [%(threadName)s] %(message)s',
                datefmt='%d-%m-%Y %H:%M:%S')
            file_item_handler.setFormatter(file_item_format)
            logger.addHandler(file_item_handler)
            item.logger = logger

    def _start_browser(self):
        if self.config['amazon.auth.user'] is None or \
                self.config['amazon.auth.password'] is None or \
                not self.config['amazon.auth.user'] or \
                not self.config['amazon.auth.password']:
            self.tech_logger.error(self.localization.bad_amazon_auth_config)
            if self.ui is not None:
                self.ui.onAmazonLoginError()
            # In the case with empty amazon user/password
            # we can only track items
            self.config['general.processing'] = 'check'
            self.ready_to_track.set()
            return

        self.browser_instance = SeleniumWrapper(
            selenium_path='deps',
            block_images=True)
        self.browser_instance.set_captcha_callback(
            self.ui.onBrowserCaptcha,
            lambda: self.browser_instance.captcha_resolved.set())
        self.browser_instance.set_new_try_callback(self._browser_on_try_buy)
        is_login_success = False
        amazon_auth_traceback = None
        try:
            is_login_success = self.browser_instance.amazon_login(
                self.config['amazon.auth.user'],
                self.config['amazon.auth.password'])
        except BadAmazonLoginException:
            # TODO: implement logic
            print('BadAmazonLoginException')
            pass
        except CaptchaException:
            # TODO: implement logic
            pass
        except Exception as ex:
            amazon_auth_traceback = ''.join(
                traceback.TracebackException.from_exception(ex).format())
        if is_login_success:
            self.ready_to_track.set()
        else:
            self.tech_logger.error(self.localization.amazon_auth_error)
            if amazon_auth_traceback is not None:
                logging.error(amazon_auth_traceback)
            if self.browser_instance is not None:
                self.browser_instance.close()
                self.browser_instance = None
            if self.ui is not None:
                self.ui.onAmazonLoginError()
            # In the case with wrong amazon authentication
            # we can only track items
            self.config['general.processing'] = 'check'
            self.ready_to_track.set()
            return

        browser_waiter = Thread(
            target=self._browser_wait,
            args=(),
            daemon=True)
        browser_waiter.name = 'browser_waiter'
        browser_waiter.start()

    def _browser_wait(self):
        while True:
            is_ready_to_process = False
            if self.config['antibot.smart_browser_behavior.enabled']:
                smart_behaviour_timer = random.randrange(
                    self.config['antibot.smart_browser_behavior.min_timer'],
                    self.config['antibot.smart_browser_behavior.max_timer'])
                is_ready_to_process = self.ready_to_process_item.wait(
                    timeout=smart_behaviour_timer)
            else:
                is_ready_to_process = self.ready_to_process_item.wait()

            if is_ready_to_process:
                processing_item = None
                for i in self.traking_items:
                    if i.status == ItemStatus.PROCESSING:
                        processing_item = i

                # Start clicking buy now button while either
                # we will get good order placing page or
                # item will become unavailable
                buy_now_result = self._browser_start_processing(
                    processing_item)

                if buy_now_result:
                    # If we got a success in "buy now" we notify over tg
                    # and ask user would he want to continue hunting or exit
                    # (if check-and-buy)

                    # SHOULDDO: Move to %s syntax
                    self._notify_over_telegram(' '.join(
                        (self.localization.telegram_item_ready_to_order,
                         item.name)))

                    autobuy_str = 'check-and-auto-buy'
                    if self.config['general.processing'] == 'check-and-buy':
                        self._wait_exit_ask(processing_item)
                    elif self.config['general.processing'] == autobuy_str:
                        # If processing mode is "check-and-auto-buy"
                        # notify over tg and try to place order

                        item_logger.critical(
                            ' '.join(
                                (self.localization.item_log_finish_buy_now,
                                 processing_item.name)))
                        self.ui.onPlaceOrder(item_name=processing_item.name)
                        order_result = True
                        try:
                            self.browser_instance.place_order(
                                processing_item,
                                self.browser_instance.try_counter)
                        except ItemUnavailableException:
                            order_result = False
                        except CaptchaException:
                            # TODO: implement logic
                            pass
                        if order_result:
                            # If place order was successfull
                            # ask user would he want to continue hunting
                            # or exit

                            # SHOULDDO: Move to %s syntax
                            self._notify_over_telegram(' '.join(
                                (self.localization.telegram_good_purchase,
                                 item.name)))
                            self._wait_exit_ask(processing_item)
                        else:
                            # I'm not sure here

                            # SHOULDDO: Move to %s syntax
                            self._notify_over_telegram(' '.join(
                                (self.localization.telegram_bad_purchase,
                                 item.name)))
                            self._return_to_track(processing_item)

                else:
                    # If we don't got a success in "buy now"
                    # (item became unavailable)
                    # we notify over tg and return to track items

                    # SHOULDDO: Move to %s syntax
                    self._notify_over_telegram(' '.join(
                        (self.localization.telegram_item_bad_proccessing,
                         item.name)))
                    self._return_to_track(processing_item)
            else:
                self.browser_instance.smart_behaviour_act()

    def _browser_start_processing(self, item):
        result = None
        # SHOULDDO: May be should change item_logger config
        # and log not a threadname, but item_name
        item.logger.critical(
            ' '.join((self.localization.item_log_start_buying_msg,
                      item.name)))
        # SHOULDDO: Move to %s syntax
        self._notify_over_telegram(' '.join(
            (self.localization.telegram_item_processing,
             item.name)))
        self.ui.onStartProcessing(item_name=item.name)
        # TODO: method start_buy_now cannot process user canceling
        # while executing (if would be called return_to_track_callback)
        # It seems I've already fixed this, check after a time
        result = True
        try:
            self.browser_instance.start_buy_now(item_url=item.url)
        except CaptchaException:
            # TODO: implement logic
            pass
        except ItemUnavailableException:
            result = False
        # TODO: show buying try number (like progress bar)
        # TODO: write logic after processing the item
        # (e.g. clear ready_to_process_item)
        # It seems I've already fixed this, check after a time
        return result

    def _prepare_env(self):
        """
        Initiate some environment variables.
        Send hello-message to telegram.
        Other things.
        """

        # Call handler before exit to clear up
        atexit.register(self._exit_handler)

        # Get localization
        self.localization = LocalizationFactory().get_localization(
            locale=self.config['general.locale'])

        # If antibot smart sleep feature is enabled initialize it
        if self.config['antibot.smart_sleep.enabled']:
            AmazonItem.init_smart_sleep(
                smart_sleep_min_timer=self.config[
                    'antibot.smart_sleep.min_timer'],
                smart_sleep_max_timer=self.config[
                    'antibot.smart_sleep.max_timer'],
                smart_sleep_min_time=self.config[
                    'antibot.smart_sleep.min_time'],
                smart_sleep_max_time=self.config[
                    'antibot.smart_sleep.max_time'])
        if self.config['general.logs.statistic']:
            AmazonItem.set_get_stats_callback(self._log_items_check_stats)

        # Configure notifyers
        self.alarm = SoundNotifyer(os.path.join(Pennyworth.script_path,
                                                Pennyworth.alarm_file_name))
        if self.config['notifyers.telegram.enabled']:
            try:
                self.telegram_bot = TelegramNotifyer(
                    self.config['notifyers.telegram.token'],
                    self.config['notifyers.telegram.chat_id'])
            except TelegramBadConfigException:
                tech_logger.error(telegram_bad_config)
                self.telegram_bot = None
        self._notify_over_telegram(self.localization.hello_msg)

    def _notify_over_telegram(self, msg):
        if self.telegram_bot is None:
            return
        try:
            self.telegram_bot.send_text(msg)
        except Exception as ex:
            tech_logger.Exception(ex)

    def _exit_handler(self):
        if self.browser_instance is not None:
            self.browser_instance.close()
        logging.shutdown()
        # Remember this:
        # sys.stderr = app_log_file
        # May be should clear this here

    def _return_to_track(self, item):
        item.status = ItemStatus.UNTRACKED
        self.ready_to_process_item.clear()
        item_tracker = Thread(
            target=item.track(),
            args=(),
            daemon=True)
        item_tracker.name = item.name
        item_tracker.start()

    def _wait_exit_ask(self, item):
        self.ui.afterProcessing(item_name=item.name,
                                exit_ask_callback=_exit_ask_callback)
        self.keep_working_answer.wait()
        self.keep_working_answer.clear()
        self._return_to_track_callback(item)

    def _exit_ask_callback(self, result):
        if result:
            sys.exit()

        self.keep_working_answer.set()

    def _browser_on_try_buy(self, try_number):
        processing_item = None
        for i in self.traking_items:
            if i.status == ItemStatus.PROCESSING:
                processing_item = i
        processing_item.logger.critical(
            ' '.join((self.localization.item_log_new_try_buy,
                      str(try_number))))
        self.ui.onBuyTry(try_number)

    def _item_check_bad_response_callback(self, status_code, context):
        """
        This is callback called while curl got bad http status.
        We use it only to create and show statistics or debug.
        Do not use it to show ERROR status in ui!
        """

        if self.file_statistic_logger is not None:
            # Log http status code from curl to statistic logger
            stat_record = ' '.join((str(context),
                                    'STATUS_CODE:',
                                    str(status_code)))
            self.file_statistic_logger.error(stat_record)

        self.ui.onBadResponseError(context=context, status_code=status_code)

    def _item_check_parse_page_error_callback(self, http_body, context):
        """
        This is callback called while curl got bad http status.
        We use it to debug if we wanna got non-expected http pages.
        (!) Use a lot of space on disk - dump all http code on page.
        Do not use it to show ERROR status in ui!
        """

        if 'discuss automated access to' in http_body:
            stat_record = ' '.join((str(context), 'PAGE: BUN'))
        else:
            stat_record = ' '.join((str(context), 'PAGE: UNEXPECTED HTML'))

        if self.file_http_logger is not None:
            http_record = ' '.join((str(context), 'PAGE:', http_body))
            # Log http body from curl to http logger
            # Possible bug
            # File "C:\pennyworth\src\pennyworth.py", line 434, in _item_check_parse_page_error_callback
            # self.file_http_logger.error(http_record)
            # Unable to print the message and arguments - possible formatting error.
            # Use the traceback above to help find the error.
            self.file_http_logger.error(http_record)

        if self.file_statistic_logger is not None:
            # Log http  code from curl to statistic logger
            self.file_statistic_logger.error(stat_record)

        self.ui.onParsePageError(context=context, http_body=None)

    def _item_check_error_callback(self, ex):
        # tb = ''.join(
        #      traceback.TracebackException.from_exception(ex.curl_ex).format())
        error_record = ' '.join((str(ex.curl_ex), str(ex.context)))
        self.tech_logger.error(error_record)

    def _item_status_changed_callback(self, item):
        if item.status == ItemStatus.UNTRACKED:
            self.ui.onItemUntracked(item_name=item.name)
        if item.status == ItemStatus.UNAVAILABLE:
            item.logger.warning(self.localization.item_log_item_unavailable)
            self.ui.onItemUnavailable(item_name=item.name)
        if item.status == ItemStatus.AVAILABLE:
            item.logger.warning(self.localization.item_log_item_available)
            self.alarm.play_sound()
            # SHOULDDO: Move to %s syntax
            self._notify_over_telegram(' '.join(
                (self.localization.telegram_item_available,
                 item.name,
                 item.url)))
            if self.config['general.processing'] != 'check':
                logger = logging.getLogger('Tech')
                logger.critical('!!!! Start process')
                item.status = ItemStatus.PROCESSING
                logger.critical('!!!! Start process 111')
                self.ready_to_process_item.set()
            self.ui.onItemAvailable(item_name=item.name)

    def _item_status_got_callback(self, item):
        if item.status is None:
            return

        debug_record = ' '.join((item.status.name))
        self.tech_logger.debug(item.status.name)

        if item.status != ItemStatus.ERROR:
            return

        if item.errors_counter in Pennyworth.item_bad_checks_count:
            item.logger.warning(self.localization.item_log_item_error)
            self.ui.onItemCheckContinuesErrors(item.name)
            if self.config['notifyers.telegram.item_eror_notify']:
                # SHOULDDO: Move to %s syntax
                self._notify_over_telegram(' '.join(
                    (self.localization.telegram_item_continues_errors,
                     item.name)))

    def _log_items_check_stats(self, item):
        if self.file_statistic_logger is not None:
            # Log item's check statistic (min, max times, etc)
            stat_record = ' '.join((item.name,
                                    'CHECK TIME STATS',
                                    'min:',
                                    str(round(min(item.stats), 2)),
                                    'max:',
                                    str(round(max(item.stats), 2)),
                                    'avg:',
                                    str(round(
                                        sum(item.stats) / len(item.stats), 2)),
                                    'stats sample count:',
                                    str(len(item.stats))))
            self.file_statistic_logger.error(stat_record)
            item.stats.clear()

    def start(self):
        self._get_config()
        self._prepare_env()

        if self.config['general.ui'] == 'tui':
            # TODO: connect UI code here
            self.ui = TUI(self.localization,
                          exit_callback=self._exit_handler)

        keep_starting = Thread(
            target=self._keep_starting,
            args=(),
            daemon=True)
        keep_starting.name = 'keep_starting'
        keep_starting.start()
        self.ui.start()

    def _keep_starting(self):
        time.sleep(1)
        self._generate_items_list()
        self._init_loggers()

        # If we only check items for availabilty
        # we don't need to work with browser
        if self.config['general.processing'] != 'check':
            # Start browser in different thread to be able load ui
            # while browser is loading
            browser_starter = Thread(
                target=self._start_browser,
                args=(),
                daemon=True)
            browser_starter.name = 'browser_starter'
            browser_starter.start()
        else:
            # If we only check items for availabilty
            # we start tracking items right now
            self.ready_to_track.set()

        self.ready_to_track.wait()

        for item in self.traking_items:
            item_tracker = Thread(
                target=item.track,
                args=(
                    self._item_check_bad_response_callback,
                    self._item_check_parse_page_error_callback,
                    self._item_check_error_callback),
                daemon=True)
            item_tracker.name = item.name
            item_tracker.start()
