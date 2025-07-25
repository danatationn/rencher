import os.path
import platform
import shutil
import subprocess
import sys
import sysconfig
import time

import cx_Freeze  # noqa: F401
import requests


def main():
    ait_path = ''
    for exec_name in ['appimagetool',
                     f'appimagetool-{platform.machine()}', 
                     f'appimagetool-{platform.machine()}.AppImage']:
        if ait_path:
            break
        if os.path.isfile(exec_name):
            ait_path = exec_name
        else:
            ait_path = shutil.which(exec_name)
    
    if ait_path:
        ait_path = os.path.abspath(ait_path)
    else:
        print('"appimagetool" couldn\'t been found in path.')
        if sys.stdin.isatty():
            print('You can either:\n'
                  '1. Download appimagetool\n'
                  '2. Specify the path to your existing appimagetool\n'
                  '3. Exit')
            
            choice = input('> ')
        else:
            choice = '1'
        
        if choice == '1':
            url = f'https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-{platform.machine()}.AppImage'
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                filename = os.path.basename(url)
                ait_path = os.path.abspath(os.path.join(__file__, '..', filename))
                
                total_size = int(r.headers['Content-Length'])
                downloaded_size = 0
                
                with open(ait_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = (downloaded_size / total_size) * 100
                        print(f'\rDownloading... {progress:.2f}%'
                              f' ({downloaded_size/1000000:.1f} / {total_size/1000000:.1f} MB)'
                              f' {url}', end='', flush=True)
            print('')
        elif choice == '2':
            while True:
                line = input('path: ')
                if line == '':
                    return
                ait_path = os.path.abspath(line)
                if os.path.isfile(ait_path):
                    break
                else:
                    print(f'{ait_path} is invalid!')
        else:
            return

    rencher_dir = os.path.abspath(os.path.join(__file__, '../..'))
    freeze_dir = os.path.join(
        rencher_dir, 'build',
        f'exe.{sysconfig.get_platform()}-{sysconfig.get_python_version()}',
    )
    if os.path.isdir(freeze_dir):
        if sys.stdin.isatty():
            choice = input('Freeze Rencher? (Y/n) ')
        else:
            choice = 'y'
        if choice.lower() in ['y', '']:
            sys.argv.append('build')
            import freeze  # noqa: F401
    else:
        print('Rencher hasn\'t been frozen yet. Freezing...')
        sys.argv.append('build')
        import freeze  # noqa: F401

    apprun_path = os.path.join(freeze_dir, 'AppRun')
    with open(apprun_path, 'w') as f:
        f.write("""#!/bin/sh
cd "$(dirname "$0")"
exec ./rencher""")

    # mark as executable
    exec_mode = os.stat(apprun_path).st_mode
    os.chmod(apprun_path, exec_mode | 0o111)

    desktop_path = os.path.join(freeze_dir, 'PKGBUILD.desktop')
    with open(desktop_path, 'w') as f:
        f.write("""[Desktop Entry]
Version=1.0
Type=Application
Name=Rencher
Comment=PKGBUILD
Exec=rencher
Icon=rencher-icon
Terminal=false
StartupNotify=false
Categories=Game;""")

    icon_path = os.path.join(rencher_dir, 'assets/rencher-icon.svg')
    target_path = os.path.join(freeze_dir, 'rencher-icon.svg')
    if not os.path.isfile(icon_path):
        raise FileNotFoundError('The icon was not found! ("rencher-icon.svg")\n'
                                'Redownload Rencher and try again')
    shutil.copy(icon_path, target_path)

    exec_mode = os.stat(ait_path).st_mode
    os.chmod(ait_path, exec_mode | 0o111)
    os.chdir(freeze_dir)
    try:
        subprocess.check_call([ait_path, './'])
    except subprocess.CalledProcessError as err:
        raise RuntimeError('AppImage creation failed.') from err
    else:
        time.sleep(.1)  # the appimagetool success message is asynchronous
        appimage_path = os.path.join(freeze_dir, 'Rencher-x86_64.AppImage')
        print(f'AppImage creation done! (it should be at {appimage_path})')

    if sys.stdin.isatty():
        choice = input('Launch it? (Y/n) ')
    else:
        choice = 'n'
    if choice.lower() in ['y', '']:
        if not os.path.isfile(appimage_path):
            raise FileNotFoundError('The file doesn\'t exist apparently? Try and find it yourself. :(')

        subprocess.run(appimage_path)

if __name__ == '__main__':
    main()