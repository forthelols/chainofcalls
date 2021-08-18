import chainofcalls


class TestChainOfCalls:
    def test_simple_calls(self):
        """Test that two calls in series work as they should"""

        @chainofcalls.output("b")
        def create_tarball(a):
            return a + 1

        @chainofcalls.output("c")
        def sign_artifact(b):
            return b + 2

        chain = chainofcalls.ChainOfCalls()

        chain.append(create_tarball)
        chain.append(sign_artifact)

        chain.args["a"] = 1
        chain.execute()

        assert chain.success_on_last_run
        assert chain.a == 1
        assert chain.b == 2
        assert chain.c == 4

    def test_unpacking_output(self):
        """Test unpacking the output of a function into multiple objects"""

        @chainofcalls.output("a", "b")
        def foo():
            return 1, "one"

        chain = chainofcalls.ChainOfCalls()
        chain.append(foo)
        chain.execute()

        assert chain.a == 1
        assert chain.b == "one"

    def test_mapping_input(self):
        """Test mapping input names from the function to be called to the names known to the cahin object"""

        @chainofcalls.map_arguments(a="another_arg")
        @chainofcalls.output("result")
        def foo(a):
            return a + 1

        chain = chainofcalls.ChainOfCalls()
        chain.append(foo)
        chain.args["another_arg"] = 1
        chain.args["a"] = 10
        chain.execute()

        assert chain.result == 2

    def test_string_representation(self):
        """Test the string representation of a chain of calls"""

        @chainofcalls.output("b")
        def create_tarball(a):
            return a + 1

        @chainofcalls.output("c")
        def sign_artifact(b):
            return b + 2

        @chainofcalls.output("c")
        def compute_sha256(b):
            return b + 2

        chain = chainofcalls.ChainOfCalls()
        chain.args["a"] = 1
        chain.append(create_tarball)
        chain.append(sign_artifact)
        chain.append(compute_sha256)

        output = str(chain)
        assert output == "create_tarball -> sign_artifact -> compute_sha256"

    def test_simple_cleanup(self):
        """Test we can register and run cleanup functions"""
        cleanup_called = False

        @chainofcalls.output("a")
        def foo():
            return 1

        @foo.cleanup()
        def _cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        chain = chainofcalls.ChainOfCalls()
        chain.append(foo)
        chain.execute()

        assert cleanup_called

    def test_simple_error(self):
        """Test we can register and run error handlers"""
        on_error_called = False

        @chainofcalls.action
        def foo():
            raise RuntimeError("Oops!")

        @foo.on_error()
        def _on_error():
            nonlocal on_error_called
            on_error_called = True

        chain = chainofcalls.ChainOfCalls()
        chain.append(foo)
        chain.execute()

        assert on_error_called

    def test_error_and_cleanup_in_the_middle(self):
        """Test that we call error handlers and cleanup functions for actions that started execution"""
        foo_cleanup_called, foo_on_error_called = False, False
        bar_cleanup_called, bar_on_error_called = False, False

        @chainofcalls.action
        def foo():
            raise RuntimeError("Oops!")

        @foo.on_error()
        def _foo_on_error():
            nonlocal foo_on_error_called
            foo_on_error_called = True

        @foo.cleanup()
        def _foo_cleanup():
            nonlocal foo_cleanup_called
            foo_cleanup_called = True

        @chainofcalls.action
        def bar():
            pass

        @bar.on_error()
        def _bar_on_error():
            nonlocal bar_on_error_called
            bar_on_error_called = True

        @bar.cleanup()
        def _bar_cleanup():
            nonlocal bar_cleanup_called
            bar_cleanup_called = True

        chain = chainofcalls.ChainOfCalls()
        chain.append(foo)
        chain.append(bar)
        chain.execute()

        assert foo_cleanup_called
        assert foo_on_error_called
        assert not bar_cleanup_called
        assert not bar_on_error_called

        assert not chain.success_on_last_run
        assert str(chain.exception) == "Oops!"

    def test_add_plain_functions(self):
        number_of_calls = 0

        def foo():
            nonlocal number_of_calls
            number_of_calls += 1

        def bar():
            nonlocal number_of_calls
            number_of_calls += 1

        chain = chainofcalls.ChainOfCalls()
        chain.append(foo)
        chain.append(bar)
        chain.execute()

        assert number_of_calls == 2
