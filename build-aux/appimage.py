"""
    # todo
        * auto download appimagetool if not found
        * fix the "AppStream upstream metadata is missing, please consider creating it" warning
"""
import os.path
import shutil
import subprocess
import sys
import sysconfig
import time


def main():
    exec_name = 'appimagetool'
    while True:
        if os.path.isfile(exec_name):
            ait_path = exec_name
        else:
            ait_path = shutil.which(exec_name)
        if ait_path:
            print(f'Found at "{ait_path}"!')
            break
        elif sys.stdin.isatty():
            print(f'"{exec_name}" was not found in path!\n'
                   'Do you have it named as something else?\n'
                   '(you can type!) (paths also work!)')
            exec_name = input(' > ')
        else:
            raise FileNotFoundError(f'"{exec_name}" was not found in path!')

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

    os.chdir(freeze_dir)
    try:
        subprocess.check_call([ait_path, './'])
    except subprocess.CalledProcessError as err:
        raise RuntimeError('AppImage creation failed.') from err
    else:
        time.sleep(0.1)  # the appimagetool success message is asynchronous
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