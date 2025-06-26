<p align="center">
	<img src="public/rencher-logo.png" width="400px"/>
<p/>

rencher is a ren'py game manager, made with ddlc mods in mind

it strives to be as simple as possible, while being as beautiful as possible

[link to the trello board](https://trello.com/b/CGaqf0xx/rencher)

## running/compiling
! WARNING ! this is still *heavily* a WIP so expect bugs galore

<img src="public/Screenshot From 2025-06-26 22-25-14.png" alt="WIP Screenshot of Rencher's UI" width="512px"/>

### linux
1. install uv
2. do `uv sync`
3. run:
	* `python main.py` if you want to test it out
    * `python build.py` if you want to compile it

### windows
1. install msys2
2. install the required packages:
   ```
   pacman -S --needed --noconfirm\
        git\
		mingw-w64-ucrt-x86_64-python\
		mingw-w64-ucrt-x86_64-python-pip\
		mingw-w64-ucrt-x86_64-python-gobject\
		mingw-w64-ucrt-x86_64-blueprint-compiler\
		mingw-w64-ucrt-x86_64-gtk4\
		mingw-w64-ucrt-x86_64-libadwaita\
		mingw-w64-ucrt-x86_64-gcc\
		mingw-w64-ucrt-x86_64-python-nuitka\
		mingw-w64-ucrt-x86_64-ntldd
   ```
3. do `pip install -r requirements.txt`
4. run:
	* `python main.py` if you want to test it out
	* `python build.py` if you want to compile it

## license

logo made by my good man [vl1](https://vl1.neocities.org/) . check him out!

[GNU General Public License 3.0](https://github.com/danatationn/rencher?tab=GPL-3.0-1-ov-file)

© 2025 danatationn