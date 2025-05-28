# some notes i've made while figuring out compiling

## general info
nuitka only packages dlls necessary for `gi`. it does not do anything about gtk or adwaita
<br>
if you copy & paste the msys2 `bin/` folder onto `main.dist/` then it magically starts working
<br>
nuitka doesn't pacakge *all* the dlls . i need to figure out which of them need to be included

### compiling for linux
1. install uv
2. do `uv sync`
3. run `python build.py`

### compiling for windows
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