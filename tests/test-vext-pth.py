import os
import unittest

from vext.install import DEFAULT_PTH_CONTENT


class TestVextPTH(unittest.TestCase):
    # Preliminary test, that verifies that
    def test_can_exec_pth_content(self):
        # Stub test, verify lines starting with 'import' in the pth can
        # be exec'd and doesn't raise any exceptions.

        # TODO, mock file.write and get content directly from create_pth
        # instead of getting it directly from DEFAULT_PTH_CONTENT
        lines = DEFAULT_PTH_CONTENT.splitlines()

        for line in lines:
            if line.startswith("import ") or line.startswith("import\t"):
                exec(line)


if __name__ == "__main__":
    unittest.main()
