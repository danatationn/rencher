# Rencher - yet another mod manager
<p align="center">
	<img src="public/rencher-logo.png" width="400px"/>
<p/>

rencher is a ren'py game manager, made with ddlc mods in mind
<br/>
it strives to be as simple as possible, while being as beautiful as possible

[link to the trello board](https://trello.com/b/CGaqf0xx/rencher)

> [!WARNING]
> because of how rencher is packaged, windows will flag it as a virus.
> i will try to fix this in the future, but the only thing *you* can do right now is exclude it in your antivirus software
<br/>
<p>
	<img src="public/Screenshot From 2025-06-28 19-05-48.png" alt="Screenshot of Rencher's UI" width="384px"/>
	<img src="public/Screenshot From 2025-07-01 17-11-18.png" alt="Screenshot of Rencher's UI" width="384px"/>
</p>

## download!
### [windows](https://github.com/danatationn/Rencher/releases/latest/download/Rencher.exe) - [linux](https://github.com/danatationn/Rencher/releases/latest/download/Rencher) - ~~macos~~ (soon)

## tips
* in order to stop windows from thinking rencher is a virus, you can try the following:
  * bring rencher back from quarantine, move it where you need it and exclude it
  * turn off cloud protection (idk why this works)
  * exclude C:\ (not recommended)
* you can turn the update toasts in the settings ^^
* if you're importing an already set up ddlc mod, then import it and set it to mod ddlc

## possible upcoming features
- [ ] store (vndb, itch.io, the old ddmc mod list thing)
- [ ] asset viewer (unrpa + unrpyc)
- [ ] discord rpc
- [ ] more...

## compiling
> [!NOTE]
> rencher is currently going through major backend reworks
> if you want to compile it, then please switch to the v1.0.2 tag
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