# platform-apollo3blue: Apollo3Blue development platform for platformio.
# Copyright 2019-present NigelB
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
from os import makedirs
from os.path import isdir, join, basename

from SCons.Script import (ARGUMENTS, COMMAND_LINE_TARGETS, AlwaysBuild,
                          Builder, Default, DefaultEnvironment)


env = DefaultEnvironment()
platform = env.PioPlatform()

env.Replace(
    AR='arm-none-eabi-ar',
    AS='arm-none-eabi-as',
    CC='arm-none-eabi-gcc',
    CXX='arm-none-eabi-g++',
    GDB='arm-none-eabi-gdb',
    OBJCOPY='arm-none-eabi-objcopy',
    RANLIB='arm-none-eabi-ranlib',
    SIZETOOL='arm-none-eabi-size',

    ARFLAGS=['rc'], # rcsP in platform.txt

    SIZEPROGREGEXP=r'^(?:\.text|\.data|\.rodata|\.text.align|\.ARM.exidx)\s+(\d+).*', # different from platform.txt
    SIZEDATAREGEXP=r'^(?:\.data|\.bss|\.noinit)\s+(\d+).*',
    SIZECHECKCMD='$SIZETOOL -A -d $SOURCES',
    SIZEPRINTCMD='$SIZETOOL -B -d $SOURCES',

    PROGSUFFIX='.axf'
)

env.Append(
    BUILDERS=dict(
        AxfToBin=Builder(
            action=env.VerboseAction(' '.join([
                '$OBJCOPY',
                '-O',
                'binary',
                '$SOURCES',
                '$TARGET'
            ]), 'Building $TARGET'),
            suffix='.bin'
        ),
        AxfToHex=Builder(
            action=env.VerboseAction(' '.join([
                '$OBJCOPY',
                '-O',
                'ihex',
                '$SOURCES',
                '$TARGET'
            ]), 'Building $TARGET'),
            suffix='.hex'
        )
    )
)

if 'nobuild' in COMMAND_LINE_TARGETS:
    target_axf = join('$BUILD_DIR', '${PROGNAME}.axf')
    target_bin = join('$BUILD_DIR', '${PROGNAME}.bin')
else:
    target_axf = env.BuildProgram()
    target_bin = env.AxfToBin(join('$BUILD_DIR', '${PROGNAME}'), target_axf)


AlwaysBuild(env.Alias('nobuild', target_axf))
target_buildprog = env.Alias('buildprog', target_axf, target_axf)

target_size = env.AddPlatformTarget(
    'size',
    target_axf,
    env.VerboseAction('$SIZEPRINTCMD', 'Calculating size $SOURCE'),
    'Program Size',
    'Calculate program size',
)

FRAMEWORK_DIR = platform.get_package_dir('framework-arduinoapollo3')

arduino_os_name = {
    'win32': 'windows',
    'linux': 'linux',
    'darwin': 'macosx'
}[sys.platform.lower()]

upload_protocol = env.subst('$UPLOAD_PROTOCOL')

def upload_program(protocol):
    program = join(FRAMEWORK_DIR, 'tools', 'uploaders', protocol, 'dist', arduino_os_name, protocol)
    if arduino_os_name == 'windows':
        program += '.exe'

    return program

asb_flags = [
    '--load-address-blob',
    '0x20000',
    '--magic-num',
    '0xCB',
    '-o',
    join('$BUILD_DIR', 'asb_intermediate'),
    '--version',
    '0x0',
    '--load-address-wired',
    '0xC000',
    '-i',
    '6',
    '--options',
    '0x1',
    '-b',
    115200,
    '-port',
    '$UPLOAD_PORT',
    '-r',
    '2',
    '-v',
]

upload_actions = [
    env.VerboseAction(lambda: env.AutodetectUploadPort(), 'Looking for upload port...'),
    env.VerboseAction(lambda: env.FlushSerialBuffer('$UPLOAD_PORT'), 'Toggling DTR/RTS...'), # DTR/RTS off, 0.1 sec, DTR/RTS on
    # env.VerboseAction(lambda: env.TouchSerialPort('$UPLOAD_PORT', 1200), 'Poking serial port.'),  # open/close serial at 1200 baud
    env.VerboseAction('$UPLOADCMD', 'Uploading $SOURCE')
]

upload_bauds = {
    'svl': [921600, 460800, 230400, 115200, 57600],
    'asb': [115200]
}

if not env.subst('$UPLOAD_SPEED'):
    env.Replace(UPLOAD_SPEED=upload_bauds[upload_protocol][0])
else:
    assert int(env.subst('$UPLOAD_SPEED')) in upload_bauds[upload_protocol]

if upload_protocol == 'svl':
    env.Replace(
        UPLOADER=upload_program('svl'),
        UPLOADERFLAGS=['$UPLOAD_PORT', '-b', '$UPLOAD_SPEED', '-v'],
        UPLOADCMD='"$UPLOADER" $UPLOADERFLAGS -f $SOURCE',

        BOOTLOADER_UPLOADER=upload_program('asb'),
        BOOTLOADER_UPLOADERFLAGS=asb_flags,
        BOOTLOADER_SOURCE=join(FRAMEWORK_DIR, 'tools/uploaders/svl/bootloader/gcc/artemis_module/bin/svl.bin'),

        LDSCRIPT_PATH=join(FRAMEWORK_DIR, 'tools/uploaders/svl/0x10000.ld'),
    )
    env.AddPlatformTarget(
        'bootloader',
        None,
        [
            env.VerboseAction(
                '$BOOTLOADER_UPLOADER $BOOTLOADER_UPLOADERFLAGS --bin "$BOOTLOADER_SOURCE"',
                'Burning bootloader',
            ),
        ],
        'Burn Bootloader',
    )
elif upload_protocol == 'asb':
    env.Default(UPLOAD_SPEED=115200)
    env.Replace(
        UPLOADER=upload_program('asb'),
        UPLOADERFLAGS=asb_flags,
        UPLOADCMD='"$UPLOADER" $UPLOADERFLAGS --bin $SOURCE',

        LDSCRIPT_PATH=join(FRAMEWORK_DIR, 'tools/uploaders/asb/0xC000.ld'),
    )
else:
    sys.stderr.write(f'Warning! Unknown upload protocol {upload_protocol}\n')

env.AddPlatformTarget('upload', target_bin, upload_actions, 'Upload')


Default([target_buildprog, target_size])
