"""Classes and functions to implement the chain of calls"""
import collections.abc
import functools
import inspect


class _ChainableAction:
    def __init__(self, func):
        self.func = func
        self.output = None
        self.input_mapping = {}
        self.output_names = []

        self.signature = inspect.signature(func)

    def get_input(self, argument_dict):
        """Extract the the input arguments from the dictionary passed as argument."""
        kwargs = {
            arg_name: argument_dict[self.input_mapping.get(arg_name, arg_name)]
            for arg_name in self.signature.parameters
        }
        return kwargs

    def get_output(self):
        """Return a dictionary with the output that has been produced by the last call."""
        if len(self.output_names) == 1:
            return {self.output_names[0]: self.output}

        if len(self.output_names) != len(self.output):
            msg = "output length is {0} while a length of {1} was expected"
            raise ValueError(msg.format(len(self.output), len(self.output_names)))

        kwargs = {}
        output_copy = list(self.output)
        for arg_name in reversed(self.output_names):
            kwargs[arg_name] = output_copy.pop()
        return kwargs

    def __call__(self, *args, **kwargs):
        self.output = self.func(*args, **kwargs)
        return self.output

    def __str__(self):
        return str(self.func.__name__)


def map_arguments(**kwargs):
    """Map the names of the input arguments to names known by the chain of calls"""

    def _decorator(func):
        action = func
        if not isinstance(func, _ChainableAction):
            action = _ChainableAction(func)
            functools.wraps(func)(action)
        action.input_mapping.update(kwargs)
        return action

    return _decorator


def output(*args):
    """Declare the names of the output for the chain of calls"""

    def _decorator(func):
        action = func
        if not isinstance(func, _ChainableAction):
            action = _ChainableAction(func)
            functools.wraps(func)(action)
        action.output_names.extend(args)
        return action

    return _decorator


class ChainOfCalls(collections.abc.MutableSequence):  # pylint: disable=too-many-ancestors
    """Chain a series of function calls together"""

    def __init__(self) -> None:
        self.callables = []
        self.args = {}

    def __getitem__(self, key):
        return self.callables[key]

    def __setitem__(self, key, value):
        # TODO: Check value types # pylint: disable=fixme
        self.callables[key] = value

    def __delitem__(self, key):
        del self.callables[key]

    def __len__(self):
        return len(self.callables)

    def insert(self, index, value):
        # TODO: check value types # pylint: disable=fixme
        return self.callables.insert(index, value)

    def execute(self):
        """Execute the chain of calls and update args."""
        for func in self.callables:
            input_kwargs = func.get_input(self.args)
            func(**input_kwargs)
            output_kwargs = func.get_output()
            self.args.update(output_kwargs)

    def __getattr__(self, name):
        return self.args[name]

    def __str__(self) -> str:
        return " -> ".join(str(fn) for fn in self.callables)
