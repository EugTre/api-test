
import typing
import random

class NamesGenerator:
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

    @staticmethod
    def generate_first_name(gender: str = 'male'):
        return random.choice(NamesGenerator.MALE_NAMES
                             if gender.lower().strip() == 'male' else
                             NamesGenerator.FEMALE_NAMES)

    @staticmethod
    def generate_last_name():
        return random.choice(NamesGenerator.LAST_NAMES)


class GeneratorsManager():
    """Class to register and provide access to data generator objects from various points
    in the framework (e.g. for compiler procedures)."""

    def __init__(self):
        self.collection = {}
        self.cache = {}

    def register(self, generator: callable, name: str = None) -> None:
        """Registers given generator under given name.

        Args:
            generator (callable): generator function.
            name (str, optional): registration name. Defaults to callable.__name__.

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
            'callable' or ('callable', 'name<str>').
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
        generator_func = self.collection[name]
        value = generator_func(*args, **kwargs)

        # Cache data if needed
        if correlation_id:
            self.cache[correlation_id] = value

        return value

generators_manager = GeneratorsManager()
generators_manager.bulk_register((
    [NamesGenerator.generate_first_name, 'FirstName'],
    [NamesGenerator.generate_last_name, 'LastName']
))
