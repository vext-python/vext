import unittest

from vext.env import findsyspy, in_venv


class TestVextAPI(unittest.TestCase):
    def test_findsyspy(self):
        # Stub test, checks no exceptions are thrown.
        findsyspy()

    def test_invenv(self):
        # Stub test, checks no exceptions are thrown.
        in_venv()


if __name__ == "__main__":
    unittest.main()
