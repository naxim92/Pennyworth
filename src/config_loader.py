import os
import yaml
from src.config_entries import *
from src.config import Config


class BadConfigFileException(Exception):
    pass


class BadConfigException(Exception):
    pass


class ConfigLoader():
    """
    Read config file (yaml).
    get_config method return config as a dictionary.
    Config dictionary has all ready-to-use configs pairs
    with defaults values.
    The config structure is defined here.
    """

    def __init__(self, config_path):
        self.config_path = config_path
        self._build_config_info()

    def _load_file(self):
        try:
            with open(self.config_path, 'r') as stream:
                self.raw_config = yaml.safe_load(stream)
        except Exception as ex:
            raise BadConfigFileException from ex

    def _build_config_info(self):
        self._config_info = Config()

        # general
        self._config_info.add_entry(ValueConfigEntry(
            name='general.locale',
            required=False,
            default='en_us'))
        self._config_info.add_entry(ValueConfigEntry(
            name='general.ui',
            required=False,
            default='tui'))
        self._config_info.add_entry(ValueConfigEntry(
            name='general.logs.level',
            required=False,
            default='ERROR',
            f_checks=[lambda x: x in ['DEBUG',
                                      'INFO',
                                      'WARNING',
                                      'ERROR',
                                      'CRITICAL']],
            exception_on_false_check=False))
        self._config_info.add_entry(ValueConfigEntry(
            name='general.logs.statistic',
            required=False,
            default=False))
        self._config_info.add_entry(ValueConfigEntry(
            name='general.logs.http_debug',
            required=False,
            default=False))
        self._config_info.add_entry(ValueConfigEntry(
            name='general.processing',
            required=True))

        # notifyers
        self._config_info.add_entry(ValueConfigEntry(
            name='notifyers.telegram.enabled',
            required=False,
            default=False))
        self._config_info.add_entry(ValueConfigEntry(
            name='notifyers.telegram.token',
            required=False))
        self._config_info.add_entry(ValueConfigEntry(
            name='notifyers.telegram.chat_id',
            required=False))
        self._config_info.add_entry(ValueConfigEntry(
            name='notifyers.telegram.item_eror_notify',
            required=False,
            default=True))

        # antibot.smart_browser_behavior
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_browser_behavior.enabled',
            required=False,
            default=False))
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_browser_behavior.min_timer',
            required=False,
            default=60))
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_browser_behavior.max_timer',
            required=False,
            default=60 * 5))
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_browser_behavior',
            required=False,
            default=False))

        # antibot.smart_sleep
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_sleep.enabled',
            required=False,
            default=True))
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_sleep.min_timer',
            required=False,
            default=900))
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_sleep.max_timer',
            required=False,
            default=1800))
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_sleep.min_time',
            required=False,
            default=8000))
        self._config_info.add_entry(ValueConfigEntry(
            name='antibot.smart_sleep.max_time',
            required=False,
            default=10000))

        # antibot proxies
        proxy_name = ValueConfigEntry(
            name='name',
            required=True)
        proxy_ip_address = ValueConfigEntry(
            name='ip_address',
            required=True,
            default='bypass')
        proxy_port = ValueConfigEntry(
            name='port',
            required=True)
        proxy_auth_user = ValueConfigEntry(
            name='auth_user',
            required=False)
        proxy_auth_pass = ValueConfigEntry(
            name='auth_pass',
            required=False)
        proxy = [proxy_name,
                 proxy_ip_address,
                 proxy_port,
                 proxy_auth_user,
                 proxy_auth_pass]
        bypass_proxy = dict()
        bypass_proxy.update({'name': 'bypass',
                             'ip_address': 'bypass',
                             'port': 0})
        self._config_info.add_entry(ListConfigEntry(
            name='antibot.proxies',
            required=False,
            default=[bypass_proxy],
            element=proxy,
            f_checks=[lambda x: len(x) > 0],
            exception_on_false_check=False))

        # amazon auth
        self._config_info.add_entry(ValueConfigEntry(
            name='amazon.auth.user',
            required=False,
            default=None,
            f_checks=[lambda x: x != ''],
            exception_on_false_check=False))
        self._config_info.add_entry(ValueConfigEntry(
            name='amazon.auth.password',
            required=False,
            default=None,
            f_checks=[lambda x: x != ''],
            exception_on_false_check=False))

        # amazon items
        item_name = ValueConfigEntry(
            name='name',
            required=True)
        item_url = ValueConfigEntry(
            name='url',
            required=True)
        item_check_interval = ValueConfigEntry(
            name='check_interval',
            required=True,
            default=2000,
            f_checks=[lambda x: x > 0])
        item = [item_name,
                item_url,
                item_check_interval]
        self._config_info.add_entry(ListConfigEntry(
            name='amazon.items',
            required=True,
            element=item,
            f_checks=[lambda x: len(x) > 0]))

    def get_config(self):
        self._load_file()
        try:
            self._config_info.generate_config(source=self.raw_config)
        except Exception as ex:
            raise BadConfigException from ex
        config_dict = self._config_info.to_dict()
        # config_dict = self.raw_config
        return config_dict


def main():
    pass
    # script_dir = os.path.dirname(os.path.realpath(__file__))
    # test_config_path = os.path.join(script_dir, '../test.yml')
    # config = ConfigLoader(test_config_path)
    # print(config.get_config())


if __name__ == '__main__':
    main()
