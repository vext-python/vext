import unittest

from vext.cmdline import do_check


class TestVextCommandLineHelpers(unittest.TestCase):
    def test_do_check(self):
        # Stub check: verifies no exceptions are thrown.
        do_check(["*"])


if __name__ == "__main__":
    unittest.main()
