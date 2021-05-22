from localization.base_localization import BaseLocalization
from localization.en_us import EN_US_Localization


class LocalizationFactory():
    """
    It is a factory for initializing localization.
    Use get_localization method to get a var with localizated messages.
    """

    @staticmethod
    def get_localization(locale='en_us'):
        """
        Build a localization class.
        Argument is a locale string like en_US (case is no matter).
        Default locale is en_US.
        """

        if locale.lower() == 'en_us':
            return EN_US_Localization()
        else:
            return BaseLocalization()
