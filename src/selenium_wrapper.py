import os
import time
import random
from threading import Event
from enum import Enum
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from src.coordinates import MouseMoveCoordinates


class BadAmazonLoginException(Exception):
    pass


class CaptchaException(Exception):
    pass


class ItemUnavailableException(Exception):
    pass


class TargetType(Enum):
    BUYNOW = 1
    PLACEORDER = 2
    LOGIN = 3
    SMARTBEHAVIOUR = 4


class SeleniumWrapper():
    """
    Work with selenium framework
    """

    _amazon_login_url = 'https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&'
    _amazon_account_page = 'https://www.amazon.com/gp/css/homepage.html'
    _amazon_main_page = 'https://www.amazon.com'
    captcha_callback = None
    captcha_callback_args = None
    new_try_callback = None

    # TODO: change selenium timeout

    def __init__(self,
                 selenium_path='deps',
                 block_images=True):
        self.selenium_path = selenium_path
        self.block_images = block_images
        self.driver = None
        self.auth_user = None
        self.auth_pass = None
        self.try_counter = 0
        self.url = None
        self.captcha_resolved = Event()
        self.target = None
        self.target_hit = Event()
        self._driver_firefox_init()

    @staticmethod
    def set_captcha_callback(callback, *args):
        SeleniumWrapper.captcha_callback = callback
        SeleniumWrapper.captcha_callback_arg = args

    @staticmethod
    def set_new_try_callback(callback):
        SeleniumWrapper.new_try_callback = callback

    def close(self):
        self.driver.close()

    def _driver_firefox_init(self):
        driver_options = Options()
        driver_profile = webdriver.FirefoxProfile()
        if self.block_images is True:
            driver_profile.set_preference('permissions.default.image', 2)
            # This doesn't work, but it seems to be a correct peace of code
            # profile.set_preference('permissions.default.stylesheet', 2)
        driver_exe = os.path.join(self.selenium_path, 'geckodriver')
        if os.name == 'nt':
            driver_exe += '.exe'
        # if viaProxy is True:
        #     # TODO: Proxylist (?)
        #     profile.set_preference("network.proxy.type", 1)
        #     profile.set_preference("network.proxy.http", proxy['host'])
        #     profile.set_preference("network.proxy.http_port", proxy['port'])
        #     profile.set_preference("network.proxy.ssl", proxy['host'])
        #     profile.set_preference("network.proxy.ssl_port", proxy['port'])
        self.driver = webdriver.Firefox(
            options=driver_options,
            executable_path=driver_exe,
            firefox_profile=driver_profile)

    # ------------------------------------------------------------------------
    # Public methods

    def amazon_login(self, user, password):
        self.target = TargetType.LOGIN
        self.try_counter = 0
        self.auth_user = user
        self.auth_pass = password
        self._get_page(SeleniumWrapper._amazon_login_url)
        self._router()
        self.target_hit.clear()
        return True

    def start_buy_now(self, item_url):
        self.target = TargetType.BUYNOW
        self.try_counter = 0
        self.url = item_url
        self._get_page(self.url)
        self._router()
        self.target_hit.clear()

    def place_order(self, item_url, try_number):
        self.target = TargetType.PLACEORDER
        self.try_counter = try_number
        self.url = item_url
        self._router()
        self.target_hit.clear()

    def smart_behaviour_act(self):
        self._rand_router()

    # ------------------------------------------------------------------------
    # Internal methods

    def _press_usd_currency_switch(self):
        self.driver.find_element_by_id('marketplaceRadio').click()

    def _press_place_order_button(self):
        self.driver.find_element_by_id('bottomSubmitOrderButtonId').click()
        self.target_hit.set()

    def _router(self):
        self._light_rand_move_mouse()
        if self._captcha_checker():
            # if this is a captcha page
            if SeleniumWrapper.captcha_callback is None:
                raise CaptchaException()
            else:
                SeleniumWrapper.captcha_callback(
                    *SeleniumWrapper.captcha_callback_arg)
                self.captcha_resolved.wait()
                self._router()
        elif not self.target_hit.is_set() and self._login_user_page_checker():
            # if this is a login page
            self._amazon_login_handler()
        elif not self.target_hit.is_set() and self._item_page_checker():
            # if this is an item page
            if self._item_availability_checker():
                self._press_buy_now_handler()
            else:
                raise ItemUnavailableException()
        elif self.target_hit.is_set():
            if self.target == TargetType.LOGIN:
                if not self._amazon_login_confirm():
                    raise BadAmazonLoginException()
            elif self.target == TargetType.BUYNOW:
                if not self._place_order_button_checker():
                    self.target_hit.clear()
                    self._router()
            elif self.target == TargetType.PLACEORDER:
                self._press_usd_currency_switch()
                webdriver.ActionChains(
                    self.driver).move_by_offset(5, 5).perform()
                self._press_place_order_button()
            return
        else:
            # if this is uknown page - just clear to imput page
            self._unknown_page_handler()

    def _rand_router(self):
        # TODO: make _rand_router
        act_list = [self._rand_move_mouse,
                    self._rand_move_mouse,
                    self._rand_scroll,
                    self._rand_scroll,
                    self._rand_get_rand_amazon_item,
                    self._rand_get_rand_amazon_item,
                    self._rand_get_rand_amazon_item,
                    lambda: self._get_page(
                        SeleniumWrapper._amazon_account_page),
                    lambda: self._get_page(
                        SeleniumWrapper._amazon_main_page),
                    lambda: self._get_page(
                        SeleniumWrapper._amazon_main_page)]
        act = random.choice(act_list)
        # print(act)
        act()

        if self._captcha_checker():
            # if this is a captcha page
            if SeleniumWrapper.captcha_callback is None:
                raise CaptchaException()
            else:
                SeleniumWrapper.captcha_callback(
                    *SeleniumWrapper.captcha_callback_arg)
                self.captcha_resolved.wait()
        elif self._login_user_page_checker():
            # if this is a login page
            self._amazon_login_handler(random_act=True)

    def _get_page(self, url):
        self.driver.get(url)

    # ------------------------------------------------------------------------
    # Checkers

    def _login_user_page_checker(self):
        # print('method _login_user_page_checker')
        try:
            self.driver.find_element_by_id('ap_email')
        except NoSuchElementException:
            # print('F')
            return False
        # print('T')
        return True

    def _captcha_checker(self):
        # print('method _captcha_checker')
        # try:
        #     probably_captcha = self.driver.find_element_by_xpath(
        #         '/html/body/comment()[1]').text
        # except NoSuchElementException:
        #     # It defenetily is not a captcha
        #     return False
        # if 'To discuss automated access to Amazon data' in probably_captcha:
        #     return True
        # return False
        try:
            self.driver.find_element_by_id('auth-captcha-image')
        except NoSuchElementException:
            return False
        return True

    def _item_page_checker(self):
        # print('method _item_page_checker')
        try:
            self.driver.find_element_by_id('productTitle')
        except NoSuchElementException:
            return False
        return True

    def _item_availability_checker(self):
        # print('method _item_availability_checker')
        try:
            self.driver.find_element_by_id('buy-now-button')
        except NoSuchElementException:
            return False
        return True

    def _buy_now_error_checker(self):
        # print('method _buy_now_error_checker')
        try:
            probably_error = self.driver.find_element_by_class_name(
                'a-spacing-mini a-spacing-top-base').text
        except NoSuchElementException:
            return False
        if 'Your Amazon Cart is empty.' in probably_error:
            return True
        return False

    def _place_order_button_checker(self):
        # print('method _place_order_button_checker')
        try:
            self.driver.find_element_by_id('bottomSubmitOrderButtonId')
        except NoSuchElementException:
            # It defenetily is a valid checkout page
            return False
        return True

    def _empty_cart_checker(self):
        # print('method _empty_cart_checker')
        if 'checkout_entry_handler' in self.driver.current_url:
            return True
        return False

    def _checkout_error_checker(self):
        # print('method _checkout_error_checker')
        try:
            probably_error = self.driver.find_element_by_class_name(
                'a-color-error').text
        except NoSuchElementException:
            return False
        if 'There was a problem' in probably_error:
            return True
        return False

    # ------------------------------------------------------------------------
    # Handlers

    def _amazon_login_handler(self, random_act=False):
        # print('method _amazon_login_handler')
        self._light_rand_move_mouse()
        self.driver.find_element_by_id('ap_email').send_keys(
            self.auth_user)
        self.driver.find_element_by_id('continue').click()
        self.driver.find_element_by_id('ap_password').send_keys(
            self.auth_pass)
        self._light_rand_move_mouse()
        self.driver.find_element_by_id('signInSubmit').click()
        if not random_act and self.target == TargetType.LOGIN:
            self.target_hit.set()
            # else: there is may be a bug
            # if target is not a Login, but we got a Login page
            # we do not confirm a succesfull login by method
            # self._amazon_login_confirm
        if not random_act:
            self._router()

    def _press_buy_now_handler(self):
        # print('method _press_buy_now_handler')
        self.driver.find_element_by_id('buy-now-button').click()
        self.target_hit.set()
        self._router()

    def _unknown_page_handler(self):
        # print('method _unknown_page_handler')
        self._default_handler()

    def _default_handler(self):
        # print('method _default_handler')
        self.try_counter += 1
        if SeleniumWrapper.new_try_callback is not None \
           and (self.target == TargetType.BUYNOW or self.target == TargetType.PLACEORDER):
            SeleniumWrapper.new_try_callback(self.try_counter)
        self._get_page(self.url)
        self._router()

    # ------------------------------------------------------------------------
    # Confirmations

    def _amazon_login_confirm(self):
        # print('method _amazon_login_confirm')
        while True:
            try:
                hello_text = self.driver.find_element_by_id(
                    'nav-link-accountList-nav-line-1').text
            except NoSuchElementException as ex:
                # print(ex)
                # print('F')
                return False
            if 'Sign in' in hello_text:
                # print(hello_text)
                # print('F')
                return False
            # print('T')
            return True

    # ------------------------------------------------------------------------
    # Random handlers

    def _light_rand_move_mouse(self):
        try:
            webdriver.ActionChains(self.driver).move_by_offset(0, 5).perform()
            time.sleep(3 / 1000)
            webdriver.ActionChains(self.driver).move_by_offset(5, -5).perform()
            webdriver.ActionChains(self.driver).move_by_offset(-5, -5).perform()
            time.sleep(5 / 1000)
            webdriver.ActionChains(self.driver).move_by_offset(-5, 5).perform()
            webdriver.ActionChains(self.driver).move_by_offset(2, 2).perform()
            time.sleep(2 / 1000)
            webdriver.ActionChains(self.driver).move_by_offset(-10, 10).perform()
        except Exception:
            pass

    def _rand_move_mouse(self):
        move = MouseMoveCoordinates(50, 50)
        c_list = move.get_random_move()
        for c in c_list:
            x, y = c
            try:
                webdriver.ActionChains(
                    self.driver).move_by_offset(x, y).perform()
            except Exception:
                pass
            time.sleep(random.randint(50, 150) / 1000)

    def _rand_scroll(self):
        y = random.randint(200, 1000)
        self.driver.execute_script(
            ''.join(('window.scrollTo(0,', str(y), ')')))

    def _rand_get_rand_amazon_item(self):
        elems = self.driver.find_elements_by_xpath("//a[@href]")
        href_list = []
        for elem in elems:
            try:
                href = elem.get_attribute("href")
                is_displayed = elem.is_displayed()
            except Exception:
                continue
            if '/dp/B0' in href \
                    and '#' not in href \
                    and is_displayed:
                href_list.append(elem)
                # print(elem.get_attribute("href"))
        if len(href_list) == 0:
            # If there are no appropriate links
            # I think it isn't often case
            self._get_page(SeleniumWrapper._amazon_main_page)
            elems = self.driver.find_elements_by_xpath("//a[@href]")
            for elem in elems:
                try:
                    href = elem.get_attribute("href")
                    is_displayed = elem.is_displayed()
                except Exception:
                    continue
                if '/dp/B0' in href \
                        and '#' not in href \
                        and is_displayed:
                    href_list.append(elem)
        elem = random.choice(href_list)
        # print(elem.get_attribute("href"))
        action = ActionChains(self.driver)
        try:
            # There is a bug here
            # https://bugzilla.mozilla.org/show_bug.cgi?id=1448825
            self.driver.execute_script(
                'arguments[0].scrollIntoView(true);', elem)
            action.move_to_element(elem).perform()
            elem.click()
        except Exception:
            pass
        self._rand_move_mouse()
