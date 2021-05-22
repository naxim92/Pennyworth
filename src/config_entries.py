class EmptyNameEntryException(Exception):
    pass


class NoValueRequiredEntryException(Exception):
    pass


class FalseCheckEntryException(Exception):
    pass


class NoneElementsListEntryException(Exception):
    pass


class ValueConfigEntry():
    """
    Define an entry in a config file, which value is just single value.
    """

    def __init__(
            self,
            name,
            required=False,
            default=None,
            f_checks=[],
            exception_on_false_check=True):
        if name is None or not name:
            raise EmptyNameEntryException()
        self.name = name
        self.required = required
        self.default = default
        self.f_checks = f_checks
        self.exception_on_false_check = exception_on_false_check

    def get_real_value(
            self,
            raw_value
    ):
        value = None
        if raw_value is None:
            if self.default is None and self.required:
                raise NoValueRequiredEntryException(self.name)
            return self.default
        value = raw_value

        for func in self.f_checks:
            if not func(value):
                if self.exception_on_false_check:
                    FalseCheckEntryException(self.name)
                else:
                    value = self.default

        return value


# ListConfigEntry(
#                 name='proxies',
#                 required=False,
#                 default=[],
#                 element=[],
#                 f_checks=[]
class ListConfigEntry():
    """
    Define an entry in a config file, which value is a list.
    Element option can be a list of ValueConfigEntry or just ValueConfigEntry.
    Element option describes element's structure.
    """

    def __init__(
            self,
            name,
            required=False,
            default=None,
            element=None,
            f_checks=[],
            exception_on_false_check=True):
        if name is None or not name:
            raise EmptyNameEntryException()
        self.name = name
        self.required = required
        self.default = default
        self.f_checks = f_checks
        self.exception_on_false_check = exception_on_false_check
        if element is None or len(element) == 0:
            raise NoneElementsListEntryException(self.name)
        self.element = element
        self._value_list = []

    def get_real_value(
            self,
            raw_value
    ):
        if raw_value is None:
            if self.default is None and self.required:
                raise NoValueRequiredEntryException(self.name)
            return self.default

        if not isinstance(self.element, list):
            for i in raw_value:
                self._value_list.append(self.element.get_real_value(i))
        else:
            for i in raw_value:
                elem = {}
                for k in self.element:
                    elem.update(
                        {k.name:
                         k.get_real_value(i.get(k.name))})
                self._value_list.append(elem)

        for func in self.f_checks:
            if not func(self._value_list):
                if self.exception_on_false_check:
                    FalseCheckEntryException(self.name)
                else:
                    return self.default

        return self._value_list
