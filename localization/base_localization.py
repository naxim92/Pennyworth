class BaseLocalization():
    """
    It is base class for all localizations.
    This class use English as the most common language.
    Use it to generate new localization.
    """

    hello = 'Hello!'
    hello_msg = 'I\'m Pennyworth. I will help you buy your wishes on Amazon. Good luck and have fun!'
    quit_prompt = 'Press Q for quit.'
    form_title = 'Pennyworth - Amazon helper bot'
    items_panel_title = 'Items\' status'
    page_parse_error = 'Page parse error, may be you\'re bunned. Details are in http log.'
    bad_response_error = 'We got bad resonse from curl worker. Response: '
    bad_amazon_auth_config = 'Empty or missing Amazon user/password in config. We cannot buy items, only track'
    amazon_auth_error = 'We got an error while Amazon login, we could only track items'
    item_log_start_buying_msg = 'We try to buy'
    item_log_finish_buy_now = 'We try to place order'
    telegram_bad_config = 'We cannot use telegram notifications. Something is wrong in config'
    telegram_item_continues_errors = 'ERROR:'
    telegram_item_available = 'AVAILABLE:'
    telegram_item_processing = 'Start processing:'
    telegram_item_ready_to_order = 'We are ready to place order:'
    telegram_item_bad_proccessing = 'Sorry, item became UNAVALABLE:'
    telegram_good_purchase = 'WOW! We\'ve bought it:'
    telegram_bad_purchase = 'Sorry, we couldn\'t do a purchase:'
    tui_details_box_title = 'Details'
    item_log_item_available = 'AVAILABLE'
    item_log_item_untracked = 'UNTRACKED'
    item_log_item_unavailable = 'UNAVAILABLE'
    item_log_item_error = 'ERROR'
    item_log_new_try_buy = 'Trying to buy number'
