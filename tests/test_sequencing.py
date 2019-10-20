import unittest
from typing import Generator

from multi_transaction_test_case import MultiTransactionTestCase, NonBlockingStep, Step


class TestSequencing(MultiTransactionTestCase):
    def test_basic(self):  # type: () -> None
        def one():  # type: () -> Generator[Step, None, None]
            yield Step(1)
            yield Step(2)
            yield Step(3)

        def two():  # type: () -> Generator[Step, None, None]
            yield Step(4)
            yield Step(5)
            yield Step(6)

        self.start((one, (), {}), (two, (), {}))
        self.start((two, (), {}), (one, (), {}))

    def test_interleaved(self):  # type: () -> None
        def one():  # type: () -> Generator[Step, None, None]
            yield Step(1)
            yield Step(3)
            yield Step(5)

        def two():  # type: () -> Generator[Step, None, None]
            yield Step(2)
            yield Step(4)

        self.start((one, (), {}), (two, (), {}))
        self.start((two, (), {}), (one, (), {}))

    @unittest.expectedFailure
    def test_fails_on_generator_exception(self):  # type: () -> None
        def one():  # type: () -> Generator[Step, None, None]
            yield Step(1)
            raise Exception

        def two():  # type: () -> Generator[Step, None, None]
            yield Step(2)

        self.start((one, (), {}), (two, (), {}))

    def test_blocking(self):  # type: () -> None
        def one():  # type: () -> Generator[Step, None, None]
            yield NonBlockingStep(1, 0.1)
            yield Step(4)

        def two():  # type: () -> Generator[Step, None, None]
            yield Step(2)
            yield NonBlockingStep(3, 0.1)

        self.start((one, (), {}), (two, (), {}))
        self.start((two, (), {}), (one, (), {}))
