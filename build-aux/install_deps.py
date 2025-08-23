import os
import platform
import subprocess
import sys


def run_sudo(args: list[str]):
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        print('Couldn\'t install dependencies. Elevating to super user...')
        sudo_args = ['sudo'] + args
        try:
            subprocess.check_call(sudo_args)
        except subprocess.CalledProcessError as err:
            raise RuntimeError('The installation failed anyway. (couldn\'t prompt super user?)') from err

def main() -> None:
    if sys.platform == 'win32':
        try:
            package_prefix = os.environ['MINGW_PACKAGE_PREFIX']
        except KeyError:
            raise OSError('You need to be in MSYS2!') from None
        else:
            if package_prefix != 'mingw-w64-ucrt-x86_64':
                raise OSError('You need to be using UCRT!')
            else:
                package_prefix += '-'
                distro = 'arch'
    elif sys.platform == 'linux':
        package_prefix = ''
        
        osr = platform.freedesktop_os_release()
        distro = osr.get(
            'ID_LIKE',
            osr['ID'],
        )
    else:
        raise OSError('Only Windows and Linux is currently supported!')
    
    if distro == 'arch':
        packages = [
             'git',
            f'{package_prefix}python',
            f'{package_prefix}python-pip',
            f'{package_prefix}python-gobject',
            f'{package_prefix}blueprint-compiler',
            f'{package_prefix}gtk4',
            f'{package_prefix}libadwaita',
            f'{package_prefix}gcc',
            f'{package_prefix}python-cx-freeze',
        ]
        if package_prefix:
            packages.append(f'{package_prefix}nsis')
        
        run_sudo(['pacman', '-Sy', '--needed', '--noconfirm', *packages])
    
    elif distro == 'debian':
        packages = [
            'python3-dev',
            'cmake',
            'gobject-introspection',
            'libgirepository1.0-dev',
            'libgirepository-2.0-dev',
            'libgtk-4-dev',
            'patchelf',
            'libadwaita-1-dev',
            'ccache',
            'blueprint-compiler',
            # cx-freeze
        ]
        
        run_sudo(['apt', 'update'])
        run_sudo(['apt', 'install', '-y', *packages])
        print('WARNING: Depending on what distro and what version you have you might not be able to build Rencher.\n'
              'e.g. Ubuntu 24.04 has an out of date version of libadwaita which doesn\'t include certain widgets that\n'
              'Rencher uses. Here be dragons!')
        
    elif distro == 'fedora':
        ...  # 
    
    else:
        raise OSError('Sorry but your distro isn\'t included in this script! You should try and install the packages yourself\n'  # noqa: E501
                      'Here\'s a list of the required packages:\n'
                      '"python3", "gtk", "adwaita", "gobject-introspection", "libgirepository", "cmake"')
    
    
    tmp_path = os.path.abspath(os.path.join(__file__, '../..'))
    try:
        subprocess.check_call(['pip', 'install', tmp_path])
    except subprocess.CalledProcessError as err:
        raise OSError('PyPI package installation failed.') from err
    else:
        print('Success!')
        
if __name__ == '__main__':
    main()