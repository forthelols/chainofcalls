from chainofcalls.chainofcalls import ChainOfCalls
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
