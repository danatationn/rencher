import os.path

from cx_Freeze import Executable, setup

import rencher

setup(
    name='Rencher',
    version=rencher.__version__,
    description=rencher.__description__,
    options={
        'build_exe': {
            # 'packages': ['rencher'],
            'excludes': [],
            'optimize': 2,
        },
    },
    executables=[
        Executable(
            script='rencher.py', 
            base='gui',
            target_name='rencher',
            icon=os.path.join(rencher.tmp_path, 'rencher/gtk/res/rencher.svg'),
        ),
    ],
)
