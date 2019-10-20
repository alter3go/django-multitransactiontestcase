import traceback
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from time import sleep
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from django.db import connection
from django.test import TransactionTestCase


class Step(object):
    """A step. Blocks the next step running until it completes."""

    def __init__(
        self, number  # type: int
    ):
        self.number = number


class NonBlockingStep(Step):
    """
    A step that does not block the next step running, but gets an optional head start.
    """

    def __init__(
        self,
        number,  # type: int
        head_start_seconds=0,  # type: Union[float, int]
    ):
        super(NonBlockingStep, self).__init__(number)
        self.head_start_seconds = head_start_seconds


StepGenerator = Generator[Step, None, None]
StepGeneratorFunction = Callable[..., StepGenerator]
StepGeneratorFunctionWithArguments = Tuple[
    StepGeneratorFunction, Sequence[Any], Mapping[str, Any]
]
_NextStep = Optional[Union[Step, str]]


def _runner(
    gen_fn,  # type: StepGeneratorFunction
    args,  # type: List[Any]
    kwargs,  # type: Dict[str, Any]
    coordinator,  # type: Connection
):
    # type: (...) -> None
    """Generator runner"""
    try:
        for step in gen_fn(*args, **kwargs):
            # Tell the parent about the next step we want to run
            coordinator.send(step)
            # Wait to be told to begin the step
            coordinator.recv()
        # Indicate the end of the last step
        coordinator.send(None)
    except BaseException:
        coordinator.send(traceback.format_exc())


class MultiTransactionTestCase(TransactionTestCase):
    def _prepare(self):  # type: () -> None
        # Close the DB connection so each process opens its own
        connection.close()

    def start(
        self, *transaction_generator_fns  # type: StepGeneratorFunctionWithArguments
    ):  # type: (...) -> None
        self._prepare()

        self._processes = {}  # type: Dict[Process, Connection]

        for gen_fn, args, kwargs in transaction_generator_fns:
            child, parent = Pipe(True)
            p = Process(target=_runner, args=(gen_fn, args, kwargs, parent))
            p.start()
            self._processes[p] = child

        try:
            self._run_steps()
        finally:
            for p in self._processes:
                p.terminate()
                p.join()

    def _run_step(
        self,
        child,  # type: Connection
        next_step,  # type: Step
    ):  # type: (...) -> Step
        # Start the next step
        child.send(None)
        if isinstance(next_step, NonBlockingStep):
            # Don't wait to hear back from the current step, but do
            # wait for its operation
            sleep(next_step.head_start_seconds)
        else:
            # Wait until the end of the current step
            next_step = child.recv()
            if isinstance(next_step, str):
                self.fail(next_step)
        return next_step

    def _handle_thing(
        self,
        next_step,  # type: Optional[Step]
        p,  # type: Process
        child,  # type: Connection
    ):  # type: (...) -> None
        if next_step is None:
            # The generator is done; wait for its process to finish
            p.join()
            del self._processes[p]
        else:
            self._waiting_steps[next_step.number] = (next_step, p, child)
            self._waiting_processes[p] = True

    def _run_steps(self):  # type: () -> None
        self._waiting_steps = (
            {}
        )  # type: MutableMapping[int, Tuple[Step, Process, Connection]]
        self._waiting_processes = {}  # type: MutableMapping[Process, bool]
        next_step_number = 1  # type: int

        while self._processes:
            for p in list(self._processes):
                child = self._processes[p]
                # Find out about the next step the child wants to run
                next_step = child.recv()  # type: _NextStep
                if isinstance(next_step, str):
                    self.fail(next_step)
                else:
                    while next_step and next_step.number == next_step_number:
                        next_step_number += 1
                        next_step = self._run_step(child, next_step)
                    self._handle_thing(next_step, p, child)
                # Check if we already know about the next step we want to run
                while next_step_number in self._waiting_steps:
                    next_step, p, child = self._waiting_steps[next_step_number]
                    del self._waiting_steps[next_step_number]
                    del self._waiting_processes[p]
                    next_step_number += 1
                    next_step = self._run_step(child, next_step)
                    self._handle_thing(next_step, p, child)
