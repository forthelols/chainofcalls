"""Classes and functions to implement the chain of calls"""
import collections.abc
import functools
import inspect


class _ChainableAction:
    def __init__(self, func):
        self.func = func
        self.input = None
        self.output = None
        self.input_mapping = {}
        self.output_names = []
        self.on_error_func = None
        self.cleanup_func = None

    def extract_input(self, argument_dict):
        """Extract the the input arguments from the dictionary passed as argument."""
        kwargs = {
            arg_name: argument_dict[self.input_mapping.get(arg_name, arg_name)]
            for arg_name in inspect.signature(self.func).parameters
        }
        return kwargs

    def output_dict(self):
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

    def cleanup(self):
        """Register a function to be run during cleanup"""

        def _decorator(func):
            self.cleanup_func = func
            return func

        return _decorator

    def on_error(self):
        """Register a function to be run if an error occurs"""

        def _decorator(func):
            self.on_error_func = func
            return func

        return _decorator

    def __call__(self, *args, **kwargs):
        self.input = {"args": args, "kwargs": kwargs}
        self.output = self.func(*args, **kwargs)
        return self.output

    def __str__(self):
        return str(self.func.__name__)


def map_arguments(**kwargs):
    """Map the names of the input arguments to names known by the chain of calls"""

    def _decorator(func):
        return_value = action(func)
        return_value.input_mapping.update(kwargs)
        return return_value

    return _decorator


def output(*args):
    """Declare the names of the output for the chain of calls"""

    def _decorator(func):
        return_value = action(func)
        return_value.output_names.extend(args)
        return return_value

    return _decorator


def action(func):
    """Wrap a callable in a chainable action object."""
    return_value = func
    if not isinstance(func, _ChainableAction):
        return_value = _ChainableAction(func)
        return_value = functools.wraps(func)(return_value)
    return return_value


class ChainOfCalls(collections.abc.MutableSequence):  # pylint: disable=too-many-ancestors
    """Chain a series of function calls together"""

    def __init__(self) -> None:
        self.callables = []
        self.args = {}
        self.success_on_last_run = None
        self.exception = None

    def __getitem__(self, key):
        return self.callables[key]

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            value = [action(f) for f in value]
        else:
            value = action(value)
        self.callables[key] = value

    def __delitem__(self, key):
        del self.callables[key]

    def __len__(self):
        return len(self.callables)

    def insert(self, index, value):
        return self.callables.insert(index, action(value))

    def execute(self):
        """Execute the chain of calls and update args."""
        called_functions = []
        try:
            for func in self.callables:
                input_kwargs = func.extract_input(self.args)
                called_functions.append(func)
                func(**input_kwargs)
                output_kwargs = func.output_dict()
                self.args.update(output_kwargs)
            self.success_on_last_run = True
        except Exception as exc:  # pylint: disable=broad-except
            self.success_on_last_run = False
            self.exception = exc
            for func in reversed(called_functions):
                if not func.on_error_func:
                    continue
                input_args, input_kwargs = func.input["args"], func.input["kwargs"]
                func.on_error_func(*input_args, **input_kwargs)
        finally:
            for func in reversed(called_functions):
                if not func.cleanup_func:
                    continue
                input_args, input_kwargs = func.input["args"], func.input["kwargs"]
                func.cleanup_func(*input_args, **input_kwargs)

    def __getattr__(self, name):
        return self.args[name]

    def __str__(self) -> str:
        return " -> ".join(str(fn) for fn in self.callables)
