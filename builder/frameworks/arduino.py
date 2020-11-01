from os.path import isdir, isfile, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir('framework-arduinoapollo3')
VARIANT_DIR = join(FRAMEWORK_DIR, 'variants', board.get('build.variant'))
CORES_DIR = join(FRAMEWORK_DIR, 'cores')

env.Append(
    ASFLAGS=[f'@{join(VARIANT_DIR, "mbed", ".asm-flags")}',
             f'@{join(VARIANT_DIR, "mbed", ".asm-symbols")}',
             f'@{join(VARIANT_DIR, "mbed", ".includes")}'],
    CCFLAGS=['-include',
             join(VARIANT_DIR, 'mbed', 'mbed_config.h'),
             '-include',
             join(CORES_DIR, 'arduino', 'sdk', 'ArduinoSDK.h'),
             '-iprefix',
             f'{CORES_DIR}/',
             f'@{join(VARIANT_DIR, "mbed", ".includes")}'],
    CFLAGS=[f'@{join(VARIANT_DIR, "mbed", ".c-flags")}',
            f'@{join(VARIANT_DIR, "mbed", ".c-symbols")}'],
    CXXFLAGS=[f'@{join(VARIANT_DIR, "mbed", ".cxx-flags")}',
              f'@{join(VARIANT_DIR, "mbed", ".cxx-symbols")}'],
    LINKFLAGS=[f'-Wl,-Map,{join("$BUILD_DIR", "program.map")}', # ???
               # f'{join(VARIANT_DIR, "mbed/libmbed-os")}.a', # covered by VARIANT_DIR in LIBPATH?
               '--specs=nano.specs',
               '$_CPPDEFFLAGS', # redundant?
               f'@{join(VARIANT_DIR, "mbed", ".ld-flags")}',
               f'@{join(VARIANT_DIR, "mbed", ".ld-symbols")}'],

    LIBPATH=[
        VARIANT_DIR,
        join(VARIANT_DIR, 'libs')
    ],

    LIBSOURCE_DIRS=[join(FRAMEWORK_DIR, 'libraries')],

    LIBS=[
        env.BuildLibrary(join('$BUILD_DIR', 'FrameworkArduinoVariant'), VARIANT_DIR),
        env.BuildLibrary(join('$BUILD_DIR', 'FrameworkArduino'), join(CORES_DIR, 'arduino')),
        env.BuildLibrary(join('$BUILD_DIR', 'FrameworkMbed'), join(CORES_DIR, 'mbed-os'), src_filter='+<*> -<TESTS/> -<TEST_APPS/> -<UNITTESTS/>'),
        env.BuildLibrary(join('$BUILD_DIR', 'FrameworkMbedBridge'), join(CORES_DIR, 'mbed-bridge')),
        env.BuildLibrary(join('$BUILD_DIR', 'FrameworkMbedBridgeCoreApi'), join(CORES_DIR, 'mbed-bridge-core-api')),
    ],

    CPPDEFINES=[
        ('ARDUINO', 10810),
        f'ARDUINO_{board.get("build.board")}',
        'ARDUINO_ARCH_MBED',
        f'ARDUINO_ARCH_{board.get("build.arch")}',
        'MBED_NO_GLOBAL_USING_DIRECTIVE',
        'CORDIO_ZERO_COPY_HCI',
    ],

    CPPPATH=[
        VARIANT_DIR,
        join(CORES_DIR, 'mbed-os'),
        join(CORES_DIR, 'arduino'),
        join(CORES_DIR, 'arduino', 'mbed-bridge'),
        join(CORES_DIR, 'arduino', 'mbed-bridge', 'core-api'),
    ],
)

env.Prepend(_LIBFLAGS="-Wl,--whole-archive ")
env.Append(_LIBFLAGS=" -Wl,--no-whole-archive -lstdc++ -lsupc++ -lm")
