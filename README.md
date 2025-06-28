<p align="center">
	<img src="public/rencher-logo.png" width="400px"/>
<p/>

rencher is a ren'py game manager, made with ddlc mods in mind
<br/>
it strives to be as simple as possible, while being as beautiful as possible

[link to the trello board](https://trello.com/b/CGaqf0xx/rencher)

## running/compiling

> [!WARNING]
> because of how rencher is packaged, windows will flag it as a virus.
> i seriously doubt i'll be able to fix this. the only thing *you* can do is exclude it in your antivirus software

rencher is nearing v1.0 ! there are some glaring bugs, but it should still be usable
<br/>
<img src="public/Screenshot From 2025-06-26 22-25-14.png" alt="Screenshot of Rencher's UI" width="512px"/>

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
		mingw-w64-ucrt-x86_64-ntldd\
        mingw-w64-ucrt-x86_64-imagemagick
   ```
3. do `pip install -r requirements.txt`
4. run:
	* `python main.py` if you want to test it out
	* `python build.py` if you want to compile it

## license

logo made by my good man [vl1](https://vl1.neocities.org/) . check him out!

[GNU General Public License 3.0](https://github.com/danatationn/rencher?tab=GPL-3.0-1-ov-file)

© 2025 danatationn