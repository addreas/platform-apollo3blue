#python mkplatform.json.py ../../packages/framework-arduinoapollo3/package_sparkfun_apollo3_index.json platform.json
import json
import sys
from argparse import ArgumentParser, FileType

parser = ArgumentParser()
parser.add_argument('input', type=FileType('r'))
parser.add_argument('output', type=FileType('w'))

host2sys = {
    'x86_64-apple-darwin': 'darwin_x86_64',
    'i386-apple-darwin11': 'darwin_i386',
    'i686-linux-gnu': 'linux_i686',
    'x86_64-pc-linux-gnu': 'linux_aarch64',
    'i686-mingw32': 'windows_x86'
}
    

def main():
    args = parser.parse_args(sys.argv[1:])
    with args.input as f:
        package_json = json.loads(f.read())

    version = '0.0.2'
    package = package_json['packages'][0]
    platforms = package['platforms']
    toolchain = package['tools'][0]

    platform = {
        'name': 'apollo3blue',
        'title': 'Apollo 3 Blue',
        'description': '',
        'engines': {
            'platformio': '<5'
        },
        'repository': {
            'type': 'git',
            'url': 'https://github.com/nigelb/platform-apollo3blue.git'
        },
        'version': version,
        'packageRepositories': [
            "https://dl.bintray.com/platformio/dl-packages/manifest.json",
            "http://dl.platformio.org/packages/manifest.json",
            {
                'framework-arduinoapollo3': [
                    {
                        'url': pl['url'],
                        'version': pl['version']
                    } for pl in platforms
                ],
            }
        ],
        'frameworks': {
            'arduino': {
                'package': 'framework-arduinoapollo3',
                'script': 'builder/frameworks/arduino.py'
            },
            'mbed': {
                'package': 'framework-mbedapollo3',
                'script': 'builder/frameworks/mbed.py'
            }
        },
        'packages': {
            'toolchain-gccarmnoneeabi': {
                'type': 'toolchain',
                'version': '>=1.7'
            },
            'framework-arduinoapollo3': {
                'type': 'framework',
                'version': '~2.0.2'
            }
        }
        
    }

    with args.output as f:
        f.write(json.dumps(platform, indent=2))



if __name__ == '__main__':
    main()
