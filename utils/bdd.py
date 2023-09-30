import allure
from allure_commons._allure import StepContext


def given(desc: str) -> StepContext:
    return allure.step(f'Given {desc}')


def when(desc: str) -> StepContext:
    return allure.step(f'When {desc}')


def then(desc: str) -> StepContext:
    return allure.step(f'Then {desc}')
