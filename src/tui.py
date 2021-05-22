# npyscreen (pip install git+https://github.com/npcole/npyscreen.git)
# windows-curses
import npyscreen
import sys
from threading import Thread
from collections import deque
from src.base_ui import BaseUI
from src.localization_factory import *
# If there are some errors with forms space - tune this one
# default: CONST_Y_SHIFT = 8
CONST_Y_SHIFT = 8
DIALOGBOX_HEIGHT = 5
DETAILSBOX_HEIGHT = 12

DETAILS_STRINGS_AMOUNT = 9


class TUI(npyscreen.StandardApp, BaseUI):

    def __init__(self, localization, exit_callback=None):
        self.loc = localization
        self.exit_callback = exit_callback
        self.details_lines = deque(maxlen=DETAILS_STRINGS_AMOUNT)
        self.items_statuses = {}
        self.dialog_lines = ['', self.loc.quit_prompt]
        self.exit_ask_callback = None
        self.error_counter = 0
        super().__init__()

    # ------------------------------------------------------------------------
    # Impementation npyscreen.StandardApp

    def onStart(self):
        self.addForm('MAIN',
                     MainForm,
                     name=self.loc.form_title)
        self._print_dialog(self.loc.hello_msg)
        # self.queue_event(npyscreen.Event("ItemStatusChanged"))

    # ------------------------------------------------------------------------
    # Impementation BaseUI

    def onParsePageError(self,
                         context,
                         http_body=None):
        self.error_counter += 1
        self.details_lines.append(' '.join((str(self.error_counter),
                                            '[Page parse error]',
                                            'proxy:',
                                            context['proxy'],
                                            'ciphers',
                                            str(context['ciphers']),
                                            'headers',
                                            str(context['headers']))))
        self.queue_event(npyscreen.Event("PrintDetails"))

    def onBadResponseError(self,
                           context,
                           status_code):
        self.error_counter += 1
        self.details_lines.append(' '.join((str(self.error_counter),
                                            '[HTTP response]',
                                            str(status_code),
                                            'proxy:',
                                            str(context['proxy']),
                                            'ciphers:',
                                            context['ciphers'],
                                            'headers',
                                            str(context['headers']))))
        self.queue_event(npyscreen.Event("PrintDetails"))

    def onAmazonLoginError(self,
                           msg=None, code=None):
        self.details_lines.append(
            'We couldn\'t login on Amazon. We can only track items now')
        self.queue_event(npyscreen.Event("PrintDetails"))

    def onBrowserCaptcha(self, callback=None):
        self._print_dialog('We got CAPTCHA. Please help me to help you, resolve CAPTCHA and press C')
        self.confirmation_callback = callback
        self.confirmation_symbols_list = ['c', 'C']
        self._add_keyboard_confirm_ask()

    def onBuyTry(self, try_number):
        self.details_lines.append('Try to buy #' + str(try_number))
        self.queue_event(npyscreen.Event("PrintDetails"))

    def onStartProcessing(self, item_name):
        self.items_statuses.update({item_name: 'PROCESSING'})
        self.queue_event(npyscreen.Event("ItemStatusChanged"))

    def onPlaceOrder(self, item_name):
        self.details_lines.append('Start processing ' + item_name)
        self.queue_event(npyscreen.Event("PrintDetails"))

    def afterProcessing(self, item_name, exit_ask_callback=None):
        self._print_dialog(''.join(('Do you want exit? (Y/N) ',
                                    'We\'ve just bought ',
                                    item_name)))
        self.exit_ask_callback = exit_ask_callback
        self._add_keyboard_yn_ask(self._y_exit_answer, self._n_exit_answer)

    def onItemUntracked(self, item_name):
        self.items_statuses.update({item_name: 'UNTRACKED'})
        self.queue_event(npyscreen.Event("ItemStatusChanged"))

    def onItemUnavailable(self, item_name):
        self.items_statuses.update({item_name: 'UNAVAILABLE'})
        self.queue_event(npyscreen.Event("ItemStatusChanged"))

    def onItemAvailable(self, item_name):
        print('method onItemAvailable')
        self.items_statuses.update({item_name: 'AVAILABLE'})
        self.queue_event(npyscreen.Event("ItemStatusChanged"))
        self.details_lines.append(' '.join((item_name, 'AVAILABLE')))
        self.queue_event(npyscreen.Event("PrintDetails"))

    def onItemCheckContinuesErrors(self, item_name):
        self.items_statuses.update({item_name: 'ERROR'})
        self.queue_event(npyscreen.Event("ItemStatusChanged"))
        # self.details_lines.append('We got errors on ' + item_name)
        # self.queue_event(npyscreen.Event("PrintDetails"))

    def start(self):
        self.run()

    # ------------------------------------------------------------------------
    # Internal methods

    def _print_dialog(self, msg):
        self.dialog_lines[0] = msg
        self.queue_event(npyscreen.Event("PrintDialog"))

    def _add_keyboard_yn_ask(self, y_callback, n_callback):
        form = self.getForm('MAIN')
        form.add_handlers({'y': self.y_callback,
                           'Y': self.y_callback,
                           'n': self.n_callback,
                           'N': self.n_callback})

    def _add_keyboard_confirm_ask(self):
        form = self.getForm('MAIN')
        confirmation_symbols_dict = dict()
        for s in self.confirmation_symbols_list:
            confirmation_symbols_dict.update({s: self._confirmation_answer})
        form.add_handlers(confirmation_symbols_dict)

    def _confirmation_answer(self, *args):
        for s in self.confirmation_symbols_list:
            self._remove_keyboard_handler(s)
        self._print_dialog(self.loc.hello_msg)
        if self.confirmation_callback is not None:
            tui_worker = Thread(
                target=self.confirmation_callback,
                args=(),
                daemon=True)
            tui_worker.name = 'tui_worker'
            tui_worker.start()
            self.confirmation_callback = None

    def _y_exit_answer(self):
        self._remove_keyboard_handler('y')
        self._remove_keyboard_handler('Y')
        self._remove_keyboard_handler('n')
        self._remove_keyboard_handler('N')
        self._print_dialog(self.loc.hello_msg)
        if self.exit_ask_callback is not None:
            self.exit_ask_callback(result='exit')
        self.exit_ask_callback = None

    def _n_exit_answer(self):
        self._remove_keyboard_handler('y')
        self._remove_keyboard_handler('Y')
        self._remove_keyboard_handler('n')
        self._remove_keyboard_handler('N')
        self._print_dialog(self.loc.hello_msg)
        if self.exit_ask_callback is not None:
            self.exit_ask_callback(result='continue')
        self.exit_ask_callback = None

    def _remove_keyboard_handler(self, symbol):
        form = self.getForm('MAIN')
        del form.handlers[symbol]


class MainForm(npyscreen.FormBaseNew):

    def create(self):
        self.loc = self.parentApp.loc
        y, x = self.useable_space()
        self.dialogBox = self.add(npyscreen.BoxTitle,
                                  rely=1,
                                  max_height=DIALOGBOX_HEIGHT,
                                  values=self.parentApp.dialog_lines)
        self.itemsStatusBox = self.add(npyscreen.BoxTitle,
                                       custom_highlighting=True,
                                       # max_height=10,
                                       max_height=y - \
                                       CONST_Y_SHIFT -\
                                       DETAILSBOX_HEIGHT,
                                       name=self.loc.items_panel_title,
                                       values=[])
        self.detailsBox = self.add(npyscreen.BoxTitle,
                                   max_height=DETAILSBOX_HEIGHT,
                                   name=self.loc.tui_details_box_title,
                                   values=[])

        self.add_handlers({'q': self._quit,
                           'Q': self._quit})
        self.add_event_hander('ItemStatusChanged',
                              self._item_status_changed_handler)
        self.add_event_hander('PrintDialog',
                              self._print_dialog_handler)
        self.add_event_hander('PrintDetails', self._print_details_box_handler)

        self.colorization = {
            'UNAVAILABLE': self.theme_manager.findPair(self, 'GOOD'),
            'AVAILABLE': self.theme_manager.findPair(self, 'WARNING'),
            'PROCESSING': self.theme_manager.findPair(self, 'DANGER'),
            'DEFAULT': self.theme_manager.findPair(self, 'DEFAULT')
        }

    def _quit(self, *args):
        if self.parentApp.exit_callback:
            self.parentApp.exit_callback()
        sys.exit()

    def _print_dialog_handler(self, event):
        element = self.dialogBox
        element.values = list(self.parentApp.dialog_lines)
        element.display()

    def _print_details_box_handler(self, event):
        element = self.detailsBox
        element.values = list(self.parentApp.details_lines)
        element.display()

    def _item_status_changed_handler(self, event):
        element = self.itemsStatusBox
        element_values = []
        element_colors = []
        for name, status in self.parentApp.items_statuses.items():
            element_values.append(name + ': ' + status)
            name_colors = [self.colorization['DEFAULT']
                           for i in name + ': ']
            status_colors = [self.colorization.get(
                status, self.colorization['DEFAULT']) for i in status]
            string_colors = name_colors
            string_colors.extend(status_colors)
            element_colors.append(string_colors)
        element.values = element_values
        element.entry_widget.highlighting_arr_color_data = element_colors
        element.display()
