from typing import Any, Mapping, Optional

from django.db import transaction

from multi_transaction_test_case import (
    MultiTransactionTestCase,
    NonBlockingStep,
    Step,
    StepGenerator,
)
from tests.testapp.models import ExampleModel


def hold_lock():  # type: () -> StepGenerator
    with transaction.atomic():
        yield Step(1)
        ExampleModel.objects.update(name="lock_holder")
        # Include an extra step to keep the transaction open
        yield Step(3)


def select_for_update(skip_locked=False):  # type: (bool) -> StepGenerator
    with transaction.atomic():
        yield NonBlockingStep(2, 0.25)
        instance = ExampleModel.objects.select_for_update(
            skip_locked=skip_locked
        ).first()
        if instance:
            instance.name = "lock_waiter"
            instance.save()


class TestSelectForUpdateSkipLocked(MultiTransactionTestCase):
    def setUp(self):  # type: () -> None
        ExampleModel.objects.create(name="initial")

    def _test_select_for_update(
        self,
        expected_name,  # type: str
        kwargs=None,  # type: Optional[Mapping[str, Any]]
    ):  # type: (...) -> None
        self.start((hold_lock, (), {}), (select_for_update, (), kwargs or {}))

        em = ExampleModel.objects.all()[0]
        assert em.name == expected_name

    def test_select_for_update(self):  # type: () -> None
        """`SELECT FOR UPDATE` should block until it obtains the lock"""
        self._test_select_for_update(expected_name="lock_waiter")

    def test_select_for_update_skip_locked(self):  # type: () -> None
        """`SELECT FOR UPDATE SKIP LOCKED` should skip locked rows"""
        self._test_select_for_update(
            expected_name="lock_holder", kwargs={"skip_locked": True}
        )
