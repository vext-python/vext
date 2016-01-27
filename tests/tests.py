import vext

# Create a temporary virtualenv and run these
import vext.env


def test_findsyspy():
    print(vext.env.findsyspy())


def test_invenv():
    print(vext.env.in_venv())

test_findsyspy()
test_invenv()
