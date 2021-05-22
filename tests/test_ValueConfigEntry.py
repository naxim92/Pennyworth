import pytest
from src.config_entries import ValueConfigEntry
from src.config_entries import EmptyNameEntryException
from src.config_entries import NoValueRequiredEntryException


class TestValueConfigEntry():
    """
    Test ValueConfigEntry class from src/config_entries.py file
    """

    @pytest.mark.parametrize(
        "name,required,default,f_checks,exception_on_false_check",
        [
            (None, False, 0, [], True),
            ('', False, 0, [], True)
        ]
    )
    def test_init_raise_excepion_given_none_name(
            self, name, required, default, f_checks, exception_on_false_check):
        """
        Test init function of a class ValueConfigEntry.
        Give no name and whatever.
        Expect raising EmptyNameEntryException.
        """

        with pytest.raises(EmptyNameEntryException):
            ValueConfigEntry(
                name=name,
                required=required,
                default=default,
                f_checks=f_checks,
                exception_on_false_check=exception_on_false_check)

    @pytest.mark.parametrize(
        "name,required,default,f_checks,exception_on_false_check",
        [
            ('test1', True, 1, [
                            (lambda x: isinstance(x, int)),
                            (lambda x: x > 0)]),
            ('test2', False, 1, []),
            ('test3', False, 1, [
                (lambda x: isinstance(x, int)),
                (lambda x: x > 0)]),
        ]
    )
    def test_get_real_value_return_value_given_different_input(
            self,
            name,
            value,
            required,
            default,
            f_checks,exception_on_false_check,
            correct_conf_fixture):
        """
        Test init function of a class ValueConfigEntry.
        Give name, value, reqired option, default value, some true checks.
        Expect getting correct value.
        """

        entry = ValueConfigEntry(
            name=name,
            value=value,
            required=required,
            default=default,
            f_checks=f_checks)
        assert entry is not None
        assert entry.name is not None and entry.name == name
        assert entry.value is not None
        if value is None and default is not None:
            assert entry.value == default
        else:
            assert entry.value == value

    def test_init_raise_excepion_given_none_value_required_none_default(self):
        """
        Test init function of a class ValueConfigEntry.
        Give name, no value, no default, required option.
        Expect raising NoValueRequiredEntryException.
        """

        with pytest.raises(NoValueRequiredEntryException):
            ValueConfigEntry(
                name='test',
                value=None,
                required=True,
                default=None,
                f_checks=[])

    def test_init_return_value_given_none_value_optional_none_default(self):
        """
        Test init function of a class ValueConfigEntry.
        Give name, no value, no default, non required option.
        Expect entry with None value.
        """

        entry = ValueConfigEntry(
            name='test',
            value=None,
            required=False,
            default=None,
            f_checks=[])
        assert entry is not None
        assert entry.name is not None and entry.name == 'test'
        assert entry.value is None
