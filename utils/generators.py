"""Generators and generator manager, to provide access to generator
collection."""
import typing
import datetime
import random
from copy import deepcopy
from string import ascii_letters, digits, ascii_lowercase

import pytest
from _pytest.mark import ParameterSet
from utils.basic_manager import BasicManager
from utils.json_content.json_wrapper import JsonWrapper


class GeneratorsManager(BasicManager):
    """Class to register and provide access to data generator objects from
    various points in the framework (e.g. for compiler procedures).

    Manager also handles cache to ensure calls to same generator with same
    correlation_id will return the very same value.
    Correlation_id is also used to set `random.seed` before generator
    function invocation (results in the same output of random)
    """
    generators = []

    def __init__(self, include_known_generators: bool = True) -> None:
        """Creates instance of GeneratorsManager class.

        Args:
            include_known_matchers (bool, optional): Flag to automatically
            register all known generators to collection. Known generators
            are generators decorated with @GeneratorsManager.register("name")
            decorator. Defaults to True.
        """
        super().__init__()
        self.cache = {}
        if include_known_generators:
            self.add_all(GeneratorsManager.generators)

    def add(self, item: typing.Callable, name: str | None = None,
            override: bool = False):
        """Registers given generator under given name.

        Args:
            item (callable): generator function.
            name (str, optional): registration name. Defaults to item.__name__.
            override (bool, optional): flag to override already registered
            names.
            Defaults to False.

        Raises:
            ValueError: when name already occupied.
        """
        return super().add(item, name, override)

    def add_all(
        self,
        items: tuple[typing.Callable, str | None] | list[typing.Callable],
        override: bool = False
    ):
        """Registers given collection of generators.

        Args:
            items (list | tuple): collection of generators where each element
            is 'callable' or ('callable', 'name<str>').
            override (bool, optional): flag to override already registered
            names. Defaults to False.
        """
        return super().add_all(items, override)

    def generate(self, name: str, args: tuple | list = (), kwargs: dict = None,
                 correlation_id: str = None) -> typing.Any:
        """Generates data using generator selected by given 'name' and using
        given 'args'/'kwargs'.

        If 'correlation_id' is given - checks for generated values in cache
        first.
        If there is no value generated yet - generates value and caches it
        under given id.

        Args:
            name (str): registered name of the generator.
            args (tuple | list, optional): generator's constructor arguments.
            Defaults to ().
            kwargs (dict, optional): generator's constructor keyword arguments.
            Defaults to None.
            correlation_id (str, optional): id used for caching/retrieving
            data from cache and setting random.seed.
            Defaults to None.

        Raises:
            ValueError: when given name is not found.

        Returns:
            typing.Any: generated value.
        """
        if name not in self.collection:
            raise ValueError(f'Failed to find generator with name "{name}"!')

        # If correlation_id is given - check for cache OR set random.seed
        if correlation_id:
            cached_id = f'{name}.{correlation_id}'
            if cached_id in self.cache:
                return self.cache[cached_id]

            random.seed(correlation_id)

        # Generate new data
        if kwargs is None:
            kwargs = {}
        generator_func = self.collection[name]
        value = generator_func(*args, **kwargs)

        # Cache data if needed
        if correlation_id:
            self.cache[cached_id] = value

        return value

    def _check_type_on_add(self, item: typing.Any):
        if callable(item):
            return

        raise ValueError(
            f'Registraion failed for item "{item}" '
            f'at {self.__class__.__name__}. '
            f'Only callable items are allowed!'
        )

    # pylint: disable=no-self-argument
    def register(name_arg):
        """Decorator function to mark generator functions.
        Marked generators will be 'known' by any created manager and
        automatically added to it's collection

        Decorator usage:
            @GeneratorManager.register("GeneratorName")
            def my_gen():
                pass
        """
        def decorator(func):
            def decorated(*args, **kwargs):
                return func(*args, **kwargs)
            GeneratorsManager.generators.append((decorated, name_arg))
            return decorated
        return decorator
    # pylint: enable=no-self-argument


# --- Generators ---
# ------------------
class FormDataGenerator:
    """Generates names from pool of names/lastnames"""
    MALE_NAMES = (
        "James",
        "John",
        "Alex",
        "Keanu",
        "Michel",
        "Aaron",
        "Richard",
        "Ricardo",
    )
    FEMALE_NAMES = (
        "Karen",
        "Kate",
        "Maria",
        "Marry",
        "Lucia",
        "Tiffany",
        "Aki",
        "Noelle"
    )
    LAST_NAMES = (
        'Harris',
        'Robinson',
        'Walker',
        'Reaves',
        'Smith',
        'Levi',
        'Yamamoto',
        'Brodski',
        'Danielopoulos',
        'McNuggets',
        'Lopez',
        'Hernandez'
    )

    @GeneratorsManager.register('FirstName')
    @staticmethod
    def generate_first_name(gender: str = 'male'):
        """Returns random first name"""
        return random.choice(FormDataGenerator.MALE_NAMES
                             if gender.lower().strip() == 'male' else
                             FormDataGenerator.FEMALE_NAMES)

    @GeneratorsManager.register('LastName')
    @staticmethod
    def generate_last_name():
        """Returns random last name"""
        return random.choice(FormDataGenerator.LAST_NAMES)

    @GeneratorsManager.register("Username")
    @staticmethod
    def generate_username(size: int = 7):
        """Generates random alphabetic sequence"""
        name = (random.choice(ascii_letters) for _ in range(size))
        return ''.join(name)

    @GeneratorsManager.register("Password")
    @staticmethod
    def generate_password(size: int = 7):
        """Generates random alphanumeric sequence"""
        passwd = (random.choice(random.choice([ascii_letters, digits]))
                  for _ in range(size))
        return ''.join(passwd)

    @GeneratorsManager.register("Sentence")
    @staticmethod
    def generate_sentence(words: int = 4):
        """Generates several 'words' of random length (3-10 chars)"""
        words = [
            ''.join([
                random.choice(ascii_lowercase)
                for _ in range(random.randint(3, 10))
            ])
            for _ in range(words)
        ]

        return ' '.join(words).capitalize()


class Dates:
    """Generates dates"""
    today = datetime.date.today()

    @staticmethod
    def get_offset(days_offset: int | tuple):
        """Returns offset timedelta"""
        if isinstance(days_offset, int):
            days_offset = (1, days_offset)
        return datetime.timedelta(days=random.randint(*days_offset))

    @GeneratorsManager.register("DateBefore")
    @staticmethod
    def generate_date_before(date: str | None = None,
                             days_offset: int | tuple = 5):
        """Generates date about 1...'days_offset' before given 'date'"""
        target_date = Dates.today if date is None else \
            datetime.date.fromisoformat(date)

        return (target_date - Dates.get_offset(days_offset)).isoformat()

    @GeneratorsManager.register("DateAfter")
    @staticmethod
    def generate_date_after(date: str | None = None,
                            days_offset: int | tuple = 5):
        """Generates date about 1...'days_offset' after given 'date'"""
        target_date = Dates.today if date is None else \
            datetime.date.fromisoformat(date)

        return (target_date - Dates.get_offset(days_offset)).isoformat()


class ParamsGenerator:
    """Generators that creates pytest parameters for
    test parametrization"""
    empty_null_ruleset = {
        "str": ["", None],
        "int": [None],
        "float": [None],
        "bool": [None],
        "dict": [{}, None],
        "list": [[], None]
    }
    data_types_ruleset = {
        "str": [124],      # [123, True, [], {}],
        "int": ["str"],    # ["string", True, [], {}],
        "float": ["str"],  # ["string", True, [], {}],
        "bool": ["str"],   # ["string", 123, [], {}],
        "dict": [123],     # ["string", 123, True, []],
        "list": [123]      # ["string", 123, True, {}],
    }

    @staticmethod
    def _apply_for(reference: dict,
                   skip: tuple | list | None,
                   callback: callable,
                   ruleset: dict | None) -> list[ParameterSet]:
        """Loops through given reference dict,
        select appropriate rule from ruleset by value type,
        and apply callback function.

        Args:
            reference (dict): data to process.
            skip (tuple | list | None): pointers to skip.
            callback (callable): function that apply rule to specific pointer.
            ruleset (dict[str, list]): ruleset with name of datatype as key
            and list of values to generate as value.

        Returns:
            list[ParameterSet]: list of pytest params
        """
        reference_content = JsonWrapper(deepcopy(reference))
        if skip is not None:
            for skipped_ptr in skip:
                reference_content.delete(skipped_ptr)

        output = []
        for ptr in reference_content.node_map:
            # Ruleset not present:
            if ruleset is None:
                result = callback(
                    JsonWrapper(deepcopy(reference)), ptr
                )
                if result is not None:
                    output.append(result)

                continue

            # Ruleset present case:
            val = reference_content.get(ptr)
            rules = ruleset[type(val).__name__]
            for rule_value in rules:
                # Note: Currently both used functions are very similar,
                # but if rule_value will be something special (like
                # generator function) - current approach will allow to
                # invoke function inside the callback
                result = callback(
                    JsonWrapper(deepcopy(reference)), ptr, rule_value
                )
                if result is not None:
                    output.append(result)

        return output

    @staticmethod
    def _empty_null_fields(content, ptr, rule_value):
        """Generate payload where given pointer will be replaced
        with rule_value and returns test param with payload and
        readable ID"""
        content.update(ptr, rule_value)
        id_name = "Empty" if isinstance(rule_value, str) else rule_value
        return pytest.param(content.get(''), id=f'{ptr}={id_name}')

    @staticmethod
    def _mixed_types_fields(content, ptr, rule_value):
        """Generate payload where given pointer will be replaced
        with rule_value and returns test param with payload and
        readable ID"""
        content.update(ptr, rule_value)
        id_name = type(rule_value).__name__
        return pytest.param(content.get(''), id=f'{ptr}={id_name}')

    @staticmethod
    def _missing_fields(content, ptr):
        """Generate payload where given pointer is missing
        and returns test param with payload and
        readable ID"""
        content.delete(ptr)
        return pytest.param(content.get(''), id=f'{ptr}=Missing')

    @staticmethod
    def get_empty_null_fields(reference: dict,
                              skip: list | tuple | None = None,
                              ruleset: dict = None,
                              ) -> list[ParameterSet]:
        """Returns list of ParameterSet with payloads
        where one of the fields is empty or null
        according to given rules

        Args:
            reference (dict): payload reference.
            skip (list | tuple, optional): pointers to nodes that must be
            skipped during generation. Defaults to None.
            ruleset (dict, optional): set of rules to apply empty/null values
            for specific type of fields. Defaults to None.

        Returns:
            list[ParameterSet]: list of pytest params for test.
        """
        if ruleset is None:
            ruleset = ParamsGenerator.empty_null_ruleset

        return ParamsGenerator._apply_for(
            reference, skip, ParamsGenerator._empty_null_fields, ruleset
        )

    @staticmethod
    def get_payloads_with_invalid_types(
        reference: dict,
        skip: list | tuple | None = None,
        ruleset: dict | None = None
    ) -> list[ParameterSet]:
        """Returns list of pytest params with payload where fields
        are populated with values of invalid data types.

        Args:
            reference (dict, optional): payload reference.
            skip (list | tuple, optional): pointers to nodes that must be
            skipped during generation. Defaults to None.
            ruleset (dict, optional): set of rules to apply empty/null values
            for specific type of fields. Defaults to None.

        Returns:
            list[ParameterSet]: list of pytest params for test.
        """
        if ruleset is None:
            ruleset = ParamsGenerator.data_types_ruleset

        return ParamsGenerator._apply_for(
            reference, skip, ParamsGenerator._mixed_types_fields, ruleset
        )

    @staticmethod
    def get_payloads_with_missing_fields(reference: dict,
                                         skip: list | tuple | None = None,
                                         ) -> list[ParameterSet]:
        """Returns list of pytest's ParameterSet with
        payloads where one of the fields is missing

        Args:
            reference (dict, optional): payload reference.
            skip (list | tuple, optional): pointers to nodes that must be
            skipped during generation. Defaults to None.

        Returns:
            list[ParameterSet]: list of pytest params for test.
        """

        return [
            pytest.param({}, id="NoFields"),
            *ParamsGenerator._apply_for(
                reference, skip, ParamsGenerator._missing_fields, None
            )
        ]


@GeneratorsManager.register("Booking")
def generate_booking():
    """Generates booking entry"""
    return {
        "firstname": FormDataGenerator.generate_first_name(),
        "lastname": FormDataGenerator.generate_last_name(),
        "totalprice": random.randint(1, 1000),
        "depositpaid": random.choice([True, False]),
        "bookingdates": {
            "checkin": Dates.generate_date_after(days_offset=2),
            "checkout": Dates.generate_date_after(days_offset=(3, 10))
        },
        "additionalneeds": FormDataGenerator.generate_sentence(5)
    }
