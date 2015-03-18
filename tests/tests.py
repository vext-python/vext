import vext

# Create a temporary virtualenv and run these
def test_findsyspy():
    vext.findsyspy()


def test_invenv():
    print(vext.in_venv())

test_findsyspy()
test_invenv()
