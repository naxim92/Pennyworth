from src.config_entries import *


class NoneConfigSource(Exception):
    pass


class Config():
    """
    Generate config from source.
    Source is a dictionary (e.g. yaml.safe_load).
    Before generate config, you should create a config ctructure.
    Do this by add_entry method.
    """

    def __init__(self, source=None):
        self._entries = []
        self.source = source
        self._config = None

    def add_entry(self, config_entry):
        """
        Add config entry to process while generating config.
        Config entry is a ValueConfigEntry or a ListConfigEntry instance.
        """

        self._entries.append(config_entry)

    def generate_config(self, source=None):
        """
        Parse source dictionary, process each config entry.
        Build ready-to-use config dictionary.
        """

        if self.source is None:
            self.source = source
        if self.source is None:
            raise NoneConfigSource()

        config = {}
        for entry in self._entries:
            config.update(
                {entry.name:
                 entry.get_real_value(self.source.get(entry.name))})
        self._config = config

    def to_dict(self):
        return self._config
