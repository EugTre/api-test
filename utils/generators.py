
import typing
import random
from abc import ABC, abstractmethod

class AbstractGenerator(ABC):
    """Test data generator"""

    @staticmethod
    @abstractmethod
    def generate():
        """Generates test data"""


class FirstNameGenerator(AbstractGenerator):
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
    @staticmethod
    def generate(gender: str = 'male'):
        return random.choice(FirstNameGenerator.MALE_NAMES
                             if gender.lower().strip() == 'male' else
                             FirstNameGenerator.FEMALE_NAMES)


class GeneratorsManager():
    """Class to register and provide access to data generator objects from various points
    in the framework (e.g. for compiler procedures)."""

    def __init__(self):
        self.collection = {}
        self.cache = {}

    def register(self, generator: AbstractGenerator, name: str = None) -> None:
        """Registers given generator under given name.

        Args:
            generator (Any): generator class.
            name (str, optional): registration name. Defaults to class.__name__.

        Raises:
            ValueError: when name already occupied.
        """
        if not name:
            name = generator.__name__

        if name in self.collection:
            raise ValueError(f'"{name}" already registered!')

        self.collection[name] = generator

    def bulk_register(self, generators: tuple|list) -> None:
        """Registers given collection of generators.

        Args:
            generators (list | tuple): collection of generators where each element is
            'class<cls>' or ('class<cls>', 'name<str>').
        """
        for generator_data in generators:
            if isinstance(generator_data, (tuple, list)):
                self.register(*generator_data)
            else:
                self.register(generator_data)

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
            raise ValueError(f'Failed to find matcher with name "{name}"!')

        # Format cache id and retrieve data from cache if present
        if correlation_id:
            correlation_id = f'{name}.{correlation_id}'
            if correlation_id in self.cache:
                return self.cache[correlation_id]

        # Generate new data
        if kwargs is None:
            kwargs = {}
        generator_cls = self.collection[name]
        value = generator_cls.generate(*args, **kwargs)

        # Cache data if needed
        if correlation_id:
            self.cache[correlation_id] = value

        return value

generators_manager = GeneratorsManager()
generators_manager.bulk_register((
    [FirstNameGenerator, 'FirstName'],
))
