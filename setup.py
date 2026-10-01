import os
import platform
import sys

# Make the version scheme module importable in PEP 517 isolated builds,
# where the project root is not on sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension

# Check for 32-bit windows builds, which currently aren't supported. We can't
# rely on `platform.architecture` here since users can still run 32-bit python
# builds on 64 bit architectures.
if sys.platform == "win32" and sys.maxsize == (2**31 - 1):
    import textwrap

    error = """
    ====================================================================
    `msgspec` currently doesn't support 32-bit Python windows builds. If
    this is important for your use case, please comment on this issue:

    https://github.com/msgspec/msgspec/issues/845
    ====================================================================
    """
    print(textwrap.dedent(error))
    exit(1)


SANITIZE = os.environ.get("MSGSPEC_SANITIZE", False)
COVERAGE = os.environ.get("MSGSPEC_COVERAGE", False)
DEBUG = os.environ.get("MSGSPEC_DEBUG", SANITIZE or COVERAGE)

extra_compile_args = []
extra_link_args = []
if SANITIZE:
    extra_compile_args.extend(["-fsanitize=address", "-fsanitize=undefined"])
    extra_link_args.extend(["-lasan", "-lubsan"])
if COVERAGE:
    extra_compile_args.append("--coverage")
    extra_link_args.append("-lgcov")
if DEBUG:
    extra_compile_args.extend(["-O0", "-g", "-UNDEBUG"])
elif sys.platform != "win32":
    extra_compile_args.extend(["-g0"])
    if sys.platform == "darwin" and platform.machine().lower() == "arm64":
        extra_compile_args.extend(["-flto=thin"])
        extra_link_args.extend(["-flto=thin"])

# from https://py-free-threading.github.io/faq/#im-trying-to-build-a-library-on-windows-but-msvc-says-c-atomic-support-is-not-enabled
# These flags are MSVC specific; other compilers used on Windows (e.g. mingw32,
# which this fork uses for local builds) reject them. They also end up on the
# link line on Python 3.8, where distutils reuses `extra_compile_args` for
# linking.
MSVC_COMPILE_ARGS = [
    "/std:c11",
    "/experimental:c11atomics",
]


class BuildExt(build_ext):
    def build_extensions(self):
        compiler_type = self.compiler.compiler_type
        for ext in self.extensions:
            if compiler_type == "msvc":
                ext.extra_compile_args.extend(MSVC_COMPILE_ARGS)
            elif sys.platform == "win32":
                # mingw-w64 does not define `_WIN64` before Python's pyconfig.h
                # is processed, so `SIZEOF_VOID_P` (and with it PyLong_SHIFT,
                # which describes CPython's PyLongObject layout) falls back to
                # the 32-bit value. Define it so the extension matches the
                # 64-bit interpreter it is built against.
                ext.extra_compile_args.append("-DMS_WIN64")
        super().build_extensions()


libraries = []
if sys.platform != "win32":
    libraries.append("m")

ext_modules = [
    Extension(
        "msgspec._core",
        [os.path.join("src", "msgspec", "_core.c")],
        libraries=libraries,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
]

setup(
    cmdclass={"build_ext": BuildExt},
    ext_modules=ext_modules,
)
