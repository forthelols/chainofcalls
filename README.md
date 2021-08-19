[![Unit tests](https://github.com/forthelols/chainofcalls/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/forthelols/chainofcalls/actions/workflows/unit_tests.yml)
[![CodeQL](https://github.com/forthelols/chainofcalls/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/forthelols/chainofcalls/actions/workflows/codeql-analysis.yml)
[![codecov](https://codecov.io/gh/forthelols/chainofcalls/branch/main/graph/badge.svg?token=Xq96LaBdak)](https://codecov.io/gh/forthelols/chainofcalls)

# chainofcalls

Construct chain of function calls in Python and defer their 
execution.

## Getting started

`chainofcalls` is a minimal Python package that permits to 
construct chains of callable objects and execute them at a 
later time. Using it is trivial:
```python
import chainofcalls

def foo():
   print('foo')

def bar():
   print('bar')

chain = chainofcalls.ChainOfCalls()
chain.append(foo)
chain.append(bar)

print(f'Calls to be executed: {chain!s}')
chain.execute()
```
Running the Python code shown above results in the following output:
```console
% python chain_hello_world.py           
Calls to be executed: foo -> bar
foo
bar
```

### Chaining functions with arguments

In many cases the functions to be chained together have more
complex signatures. With the use of a decorator we can map
a function output to one or more names. The `chain` object 
will match the names of the known outputs to the argument names 
of the next function to be called:
```python
import os.path
import chainofcalls


@chainofcalls.output('tarball')
def create_tarball(directory):
    return os.path.join(directory, 'tarball.tgz')

def ship_tarball(tarball):
    print(f'Shipping "{tarball}"')

chain = chainofcalls.ChainOfCalls()
chain.append(create_tarball)
chain.append(ship_tarball)
chain.args['directory'] = '/usr/local'
chain.execute()

print(f'Tarball path: {chain.tarball!s}')
```
Running the code above produces the following output:
```console
% python chain_output.py 
Shipping "/usr/local/tarball.tgz"
Tarball path: /usr/local/tarball.tgz
```
Any initial value needed to start the chain of call can 
be explicitly inserted in the `chain.args` dictionary.

### Cleanup and error handling
Each function in the chain can register other callables
to perform cleanup or error handling. Cleanup functions
are called at the end of the chain execution if the 
corresponding parent function was called, regardless of whether
the execution was successful or not. Error handlers are similar,
but they get called only if the execution failed:
```python
import chainofcalls

@chainofcalls.action
def foo():
    print('foo called')

@foo.on_error()
def _foo_on_error():
    print('foo error handler called')

@foo.cleanup()
def _foo_cleanup():
    print('foo cleanup called')
    
@chainofcalls.action
def bar():
    print('bar called')
    raise RuntimeError('something bad happened!')
    
@bar.on_error()
def _bar_on_error():
    print('bar error handler called')

@bar.cleanup()
def _bar_cleanup():
    print('bar cleanup called')

chain = chainofcalls.ChainOfCalls()
chain.append(foo)
chain.append(bar)
chain.execute()
```
The code above gives the following output:
```console
% python chain_error.py 
foo called
bar called
bar error handler called
foo error handler called
bar cleanup called
foo cleanup called
```
All error handlers are called before cleanup functions, if an error occurs.
In both cases the order of call is the opposite of the one used for the chain.
The rationale is that error handlers and cleanup functions represent "undo" 
operations and as such they may rely on the state created by the functions
preceding their root in the chain of calls.