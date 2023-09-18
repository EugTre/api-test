"""Tests for matchers and matcher manager

pytest -s -vv ./utils/test_generators.py
"""
import random
import pytest
import utils.generators as gen

class TestGeneratosManager:
    """Tests generators manager"""
    # Generators to use
    def simple_generator(self):
        return True

    def configurable_generator(self, a, b):
        return f'{a}/{b}'

    def heavy_configurable_generator(self, a, b, c = 'c.default', d = 'd.default'):
        return '/'.join((a,b,c,d))

    def random_generator(self, range_min = 0, range_max = 100):
        return random.randrange(range_min, range_max)

    # Tests
    def test_manager_register(self):
        manager = gen.GeneratorsManager(False)
        manager.add(self.simple_generator)

        assert manager.collection
        assert len(manager.collection) == 1

        manager.add(self.configurable_generator)
        assert len(manager.collection) == 2

    def test_manager_register_with_name(self):
        reg_name = "FooBar"
        manager = gen.GeneratorsManager(False)
        manager.add(self.simple_generator, name=reg_name)

        assert manager.collection
        assert len(manager.collection) == 1
        assert reg_name in manager

    def test_manager_register_override(self):
        manager = gen.GeneratorsManager(False)
        manager.add(self.simple_generator)

        assert manager.collection
        assert len(manager.collection) == 1

        manager.add(self.simple_generator, override=True)
        assert len(manager.collection) == 1

    def test_manager_bulk_registration(self):
        manager = gen.GeneratorsManager(False)
        manager.add_all([
            self.simple_generator,
            self.configurable_generator
        ])

        assert manager.collection
        assert len(manager.collection) == 2
        assert self.simple_generator.__name__ in manager
        assert self.configurable_generator.__name__ in manager

    def test_manager_bulk_registration_with_name(self):
        collection = [
            (self.simple_generator, 'Foo1'),
            (self.configurable_generator, 'Foo2')
        ]
        manager = gen.GeneratorsManager(False)
        manager.add_all(collection)

        assert manager.collection
        assert len(manager.collection) == 2
        assert collection[0][1] in manager
        assert collection[1][1] in manager

    def test_manager_unregister(self):
        reg_name = "FooBar"
        manager = gen.GeneratorsManager(False)
        manager.add(self.simple_generator, name=reg_name)

        assert manager.collection
        assert reg_name in manager

        op_result = manager.remove(reg_name)
        assert op_result
        assert not manager.collection
        assert reg_name not in manager

    def test_manager_generate_by_name(self):
        generator = self.simple_generator
        reg_name = "FooBar"
        manager = gen.GeneratorsManager(False)
        manager.add(generator, name=reg_name)

        assert manager.generate(reg_name)

    def test_manager_generate_by_autoname(self):
        generator = self.simple_generator
        reg_name = generator.__name__
        manager = gen.GeneratorsManager(False)
        manager.add(generator)

        assert manager.generate(reg_name)

    def test_manager_generate_with_args(self):
        generator = self.configurable_generator
        reg_name = generator.__name__
        manager = gen.GeneratorsManager(False)
        manager.add(generator)

        assert manager.generate(reg_name, ('foo', 'bar')) == 'foo/bar'

    def test_manager_generate_with_kwargs(self):
        generator = self.configurable_generator
        reg_name = generator.__name__
        manager = gen.GeneratorsManager(False)
        manager.add(generator)

        assert manager.generate(reg_name, kwargs={'a': 'foo', 'b': 'bar'}) == 'foo/bar'

    def test_manager_generate_with_mixed_args(self):
        generator = self.heavy_configurable_generator
        reg_name = generator.__name__
        manager = gen.GeneratorsManager(False)
        manager.add(generator)

        assert manager.generate(reg_name, ('foo', 'bar'), kwargs={'c': 'baz'}) \
            == 'foo/bar/baz/d.default'

    def test_manager_generate_with_correlation_id(self):
        generator = self.random_generator
        reg_name = generator.__name__
        cid = 'FooBar'

        manager = gen.GeneratorsManager(False)
        manager.add(generator)

        generated_value = manager.generate(reg_name, correlation_id=cid)
        for _ in range(10):
            assert manager.generate(reg_name, correlation_id=cid) == generated_value
        assert manager.generate(
            reg_name,
            correlation_id='BazBar',
            kwargs={'range_min': 500, 'range_max': 600}
        ) != generated_value

    def test_manager_generate_with_args_and_correlation_id(self):
        generator = self.random_generator
        reg_name = generator.__name__
        cid = 'FooBar'

        manager = gen.GeneratorsManager(False)
        manager.add(generator)

        generated_value = manager.generate(reg_name, (100, 500), correlation_id=cid)
        for i in range(10):
            assert manager.generate(reg_name, (100 * i, 500 * i), correlation_id=cid) \
                == generated_value
        assert manager.generate(reg_name, (0, 20), correlation_id='BazBar') \
            != generated_value

    # --- Negative
    def test_manager_unregister_by_invalid_name_quietly_fails(self):
        reg_name = "FooBar"
        invalid_name = "BazBar"

        manager = gen.GeneratorsManager(False)
        manager.add(self.simple_generator, name=reg_name)
        assert reg_name in manager

        op_result = not manager.remove(invalid_name)
        assert op_result
        assert reg_name in manager
        assert len(manager.collection) == 1

    def test_manager_register_duplicate_fails(self):
        manager = gen.GeneratorsManager(False)
        manager.add(self.simple_generator)

        assert manager.collection
        assert len(manager.collection) == 1

        with pytest.raises(ValueError, match=".* already registered!"):
            manager.add(self.simple_generator)

    def test_manager_register_duplicate_name_fails(self):
        manager = gen.GeneratorsManager(False)
        manager.add(self.simple_generator, "FooBar")

        assert manager.collection
        assert len(manager.collection) == 1

        with pytest.raises(ValueError, match=".* already registered!"):
            manager.add(self.configurable_generator, "FooBar")

    def test_manager_register_non_compatible_type_fails(self):
        manager = gen.GeneratorsManager(False)
        with pytest.raises(ValueError, match="Registraion failed for item.*"):
            manager.add([], "Foo")

    def test_manager_contains_fails(self):
        collection = [
            (self.simple_generator, 'Foo1'),
            (self.configurable_generator, 'Foo2'),
            (self.heavy_configurable_generator, 'Foo3')
        ]
        manager = gen.GeneratorsManager(False)
        manager.add_all(collection)

        assert 'Foo' not in manager
        assert 'Foo33' not in manager
        assert 'Bar1' not in manager


class TestGenerators:
    """Tests actual generator functions"""
    def test_names_generator_first_name_generator(self):
        assert gen.NamesGenerator.generate_first_name() in gen.NamesGenerator.MALE_NAMES

    @pytest.mark.parametrize('arg, expected', [
        ('male', gen.NamesGenerator.MALE_NAMES),
        ('female', gen.NamesGenerator.FEMALE_NAMES)
    ])
    def test_names_generator_first_name_generator_gender_specific(self, arg, expected):
        assert gen.NamesGenerator.generate_first_name(arg) in expected

    def test_names_generator_last_name_generator(self):
        assert gen.NamesGenerator.generate_last_name() in gen.NamesGenerator.LAST_NAMES
