import unittest

from vext.cmdline import do_check, do_status


class TestVextCommandLineHelpers(unittest.TestCase):
    def test_do_check(self):
        # Stub check: verifies no exceptions are thrown.
        do_check(["*"])

    def test_do_status(self):
        # Stub check: verifies no exceptions are thrown.

        # TODO, trigger different statuses and check messages printed.
        do_status()


if __name__ == "__main__":
    unittest.main()
