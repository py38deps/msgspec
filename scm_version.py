# Backport: pin the version so that building from the backport branch does
# not produce a dev version derived from git state (setuptools-scm would
# otherwise emit e.g. 0.21.2.dev30+g...).


def scheme(version):
    """Always report the pinned backport version."""
    return "0.22.0"
