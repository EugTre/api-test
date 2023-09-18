"""Generators and generator manager, to provide access generator collection them."""
import typing
import random
from utils.basic_manager import BasicManager

class GeneratorsManager(BasicManager):
    """Class to register and provide access to data generator objects from various points
    in the framework (e.g. for compiler procedures).

    Manager also handles cache to ensure calls to same generator with same correlation_id
    will return the very same value.
    """
    generators = []

    def __init__(self, include_known_generators: bool = True) -> None:
        """Creates instance of GeneratorsManager class.

        Args:
            include_known_matchers (bool, optional): Flag to automatically register all
            known generators to collection. Known generators are generators decorated
            with @GeneratorsManager.register("name") decorator. Defaults to True.
        """
        super().__init__()
        self.cache = {}
        if include_known_generators:
            self.add_all(GeneratorsManager.generators)

    def add(self, item: typing.Callable, name: str | None = None, override: bool = False):
        """Registers given generator under given name.

        Args:
            item (callable): generator function.
            name (str, optional): registration name. Defaults to item.__name__.
            override (bool, optional): flag to override already registered names.
            Defaults to False.

        Raises:
            ValueError: when name already occupied.
        """
        return super().add(item, name, override)

    def add_all(self, items: tuple[typing.Callable, str | None] | list[typing.Callable],
                override: bool = False):
        """Registers given collection of generators.

        Args:
            items (list | tuple): collection of generators where each element is
            'callable' or ('callable', 'name<str>').
            override (bool, optional): flag to override already registered names.
            Defaults to False.
        """

        print(items)
        return super().add_all(items, override)

    def generate(self, name: str, args: tuple|list = (), kwargs: dict = None,
                 correlation_id: str = None) -> typing.Any:
        """Generates data using generator selected by given 'name' and using
        given 'args'/'kwargs'.

        If 'correlation_id' is given - checks for generated values in cache first.
        If there is no value generated yet - generates value and caches it under
        given id.

        Args:
            name (str): registered name of the generator.
            args (tuple | list, optional): generator's constructor arguments. Defaults to ().
            kwargs (dict, optional): generator's constructor keyword arguments.
            Defaults to None.
            correlation_id (str, optional): id used for caching/retrieving data from cache.
            Defaults to None.

        Raises:
            ValueError: when given name is not found.

        Returns:
            typing.Any: generated value.
        """
        if name not in self.collection:
            raise ValueError(f'Failed to find generator with name "{name}"!')

        # Format cache id and retrieve data from cache if present
        if correlation_id:
            correlation_id = f'{name}.{correlation_id}'
            if correlation_id in self.cache:
                return self.cache[correlation_id]

        # Generate new data
        if kwargs is None:
            kwargs = {}
        generator_func = self.collection[name]
        value = generator_func(*args, **kwargs)

        # Cache data if needed
        if correlation_id:
            self.cache[correlation_id] = value

        return value

    def _check_type_on_add(self, item: typing.Any):
        if callable(item):
            return

        raise ValueError(f'Registraion failed for item "{item}" at {self.__class__.__name__}. '
                         f'Only callable items are allowed!')

    # pylint: disable=no-self-argument
    def register(name_arg):
        """Decorator function to mark generator functions.
        Marked generators will be 'known' by any created manager and automatically
        added to it's collection

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


class NamesGenerator:
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
        return random.choice(NamesGenerator.MALE_NAMES
                             if gender.lower().strip() == 'male' else
                             NamesGenerator.FEMALE_NAMES)

    @GeneratorsManager.register('LastName')
    @staticmethod
    def generate_last_name():
        """Returns random last name"""
        return random.choice(NamesGenerator.LAST_NAMES)
