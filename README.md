# Rencher - a Ren'Py game manager

<img src="public/Screenshot From 2025-05-24 11-12-47.png" alt="WIP Screenshot of Rencher's UI">

### why?
this was originally a ddlc mod manager because all of them suck. 

however i thought it would've been better if it supported all ren'py games

it was originally named Doki Doki Mod Swapper, then Dossier and now Rencher (Ren'py + Launcher)! 😁😁

### when?
idfk i've been trying to make this for like a year now 😭

back when it was named dossier, i tried adding way too many features and it just slowed dev down to a halt

also i didn't know anything about how to make your code good so,,

here's [a link to the trello board](https://trello.com/b/CGaqf0xx/rencher) lmao

## running/compiling
! WARNING ! this is still *heavily* a WIP so expect bugs galore

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
3. install pip packages from `requirements.txt`
4. run:
	* `python main.py` if you want to test it out
	* `python build.py` if you want to compile it

## license

[GNU General Public License 3.0](https://github.com/danatationn/rencher?tab=GPL-3.0-1-ov-file) © 2007  Free Software Foundation