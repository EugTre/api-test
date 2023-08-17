
import logging

from utils.generators import generators_manager

print(generators_manager.generate('FirstName'))
print(generators_manager.generate('FirstName', ('female', )))
print(generators_manager.generate('FirstName', ('female', ), correlation_id='abc'))
print(generators_manager.generate('FirstName', ('female', ), correlation_id='abc'))
print(generators_manager.generate('FirstName', ('female', ), correlation_id='abc'))
print(generators_manager.generate('FirstName', ('female', ), correlation_id='abc'))
print(generators_manager.cache)
"""
class Manager:
    def __init__(self):
        self.collection = {}

    def register(self, matcher, name: str = None):
        if not name:
            name = matcher.__name__
        if name in self.collection:
            raise ValueError(f'"{name}" already registered!')
        self.collection[name] = matcher

    def get(self, name, args=(), kwargs={}):
        if name not in self.collection:
            raise ValueError(f'Failed to find matcher with name "{name}"!')
        matcher = self.collection[name]
        return matcher(*args, **kwargs)

manager = Manager()
manager.register(AnyList)
manager.register(AnyListLongerThan)

m = manager.get("AnyList")
m2 = manager.get("AnyListLongerThan", kwargs={'size': 4, 'type': int})

print(m)
print(m2)
print(manager.collection)

def test_x():
    print('XXXXXXX')
    a = [
        32, 'd'
    ]

    assert a == match.AnyListLongerThan(4, int)

"""
