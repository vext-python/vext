import unittest
import vext

"""
Basically stubs right now.
"""



class TestVextAPI(unittest.TestCase):
    def test_findsyspy(self):
        vext.env.findsyspy()

    def test_invenv(self):
        vext.env.in_venv()

if __name__ == '__main__':
    unittest.main()
