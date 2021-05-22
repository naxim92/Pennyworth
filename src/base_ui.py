class NotImplementedMethod(Exception):
    pass


class BaseUI():
    """
    It's base class for implementing UI
    """

    # TODO: add support debug mode SWITCH
    # to show curl statistics
    # (onBadResponseError, onParsePageError)

    def __init__(self):
        pass

    def onParsePageError(self,
                         context,
                         http_body=None):
        raise NotImplementedMethod('onParsePageError')

    def onBadResponseError(self,
                           context,
                           status_code):
        raise NotImplementedMethod('onBadResponseError')

    def onAmazonLoginError(self,
                           msg=None,
                           code=None):
        raise NotImplementedMethod('onAmazonLoginError')

    def onBrowserCaptcha(self, callback=None):
        raise NotImplementedMethod('onBrowserCaptcha')

    def onBuyTry(self, try_number):
        raise NotImplementedMethod('onAmazonLoginError')

    def onStartProcessing(self, item_name):
        raise NotImplementedMethod('onBuyTry')

    def onPlaceOrder(self, item_name):
        raise NotImplementedMethod('onPlaceOrder')

    def afterProcessing(self, item_name, exit_ask_callback=None):
        raise NotImplementedMethod('afterProcessing')

    def onItemUntracked(self, item_name):
        raise NotImplementedMethod('onItemUntracked')

    def onItemUnavailable(self, item_name):
        raise NotImplementedMethod('onItemUnavailable')

    def onItemAvailable(self, item_name):
        raise NotImplementedMethod('onItemAvailable')

    def onItemCheckContinuesErrors(self, item_name):
        raise NotImplementedMethod('onItemCheckContinuesErrors')

    def start(self):
        raise NotImplementedMethod('start')
