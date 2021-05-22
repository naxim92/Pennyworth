from src.localization_factory import LocalizationFactory


class TestLocalizationFactory:
    """
    Test LocalizationFactory class from src/localization_factory.py file
    """

    def test_get_localization_return_not_none_given_nothing(self):
        """
        Test static function LocalizationFactory.get_localization().
        Give nothing, expect a non None object.
        """
        localization = LocalizationFactory.get_localization()
        assert localization is not None

    def test_get_localization_return_hello_message_given_nothing(self):
        """
        Test static function LocalizationFactory.get_localization().
        Give nothing, expect hello message (string) in default localization.
        """
        localization = LocalizationFactory.get_localization()
        assert isinstance(localization.hello, str), \
            'Bad default localization (Wrong hello message)'

    def test_get_localization_return_default_hello_given_bad_locale(self):
        """
        Test static function LocalizationFactory.get_localization().
        Give bad locale, expect hello message (string) in default localization.
        """
        localization = LocalizationFactory.get_localization('bad_locale')
        assert isinstance(localization.hello, str), \
            'Bad default localization, while bad locale given'

    def test_get_localization_return_hello_message_given_en_us(self):
        """
        Test static function LocalizationFactory.get_localization().
        Give en_us locale, expect hello message (string) in en_us localization.
        """
        lower_case_locale = 'en_us'
        localization = LocalizationFactory.get_localization(lower_case_locale)
        assert isinstance(localization.hello, str), \
            ''.join('Bad ',
                    lower_case_locale,
                    ' localization (Wrong hello message).',
                    ' Locale has low case style.')

        upper_case_locale = 'en_US'
        localization = LocalizationFactory.get_localization(upper_case_locale)
        assert isinstance(localization.hello, str), \
            ''.join('Bad ',
                    upper_case_locale,
                    ' localization (Wrong hello message)',
                    ' Locale has upper case style.')
