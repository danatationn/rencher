# Rencher - yet another mod manager
<p align="center">
	<img src="data/assets/rencher-logo.png" width="400px"/>
<p/>

Rencher is a Ren'Py game manager, made with DDLC mods in mind
<br/>
it strives to be as simple as possible, while being as beautiful as possible

[link to the trello board](https://trello.com/b/CGaqf0xx/rencher)
<br/>

<p>
	<img src="data/screenshots/Screenshot From 2025-11-02 17-47-53.png" alt="Screenshot of Rencher's UI showing off the main window" width="384px"/>
	<img src="data/screenshots/Screenshot From 2025-11-02 17-48-27.png" alt="Screenshot of Rencher's UI showing off the import menu" width="384px"/>

[//]: # (	<img src="data/screenshots/Screenshot From 2025-11-02 17-48-37.png" alt="Screenshot of Rencher's UI showing off the settings menu" width="384px"/>)
[//]: # (	<img src="data/screenshots/Screenshot From 2025-11-02 17-48-08.png" alt="Screenshot of Rencher's UI showing off the tasks popover" width="384px"/>)
</p>

## download!
### [Windows](https://github.com/danatationn/Rencher/releases/latest/download/RencherInstaller.exe) - [Linux](https://github.com/danatationn/Rencher/releases/latest/download/Rencher-x86_64.AppImage)

## tips
* you can turn the update toasts in the settings
* you can also delete the .zip files after importing. also in the settings
* if you're importing an already set up DDLC mod, then just import it normally

## possible upcoming features
- [ ] store (vndb, itch.io, the old DDMC mod list thing)
- [ ] asset viewer (unrpa + unrpyc)
- [ ] Discord RPC
- [ ] more...

## building / compiling
### Linux
* install pip packages
* make meson build dir with `$ meson setup [BUILDDIR] -Dprefix=$(pwd)/[BUILDDIR]/[PREFIX]` (replace the brackets with any names you want; i went with `build` and `root`)
* run `ninja -C [BUILDDIR] install`
* launch rencher by running `ninja -C [BUILDDIR] run`

<details> <summary> AppImage </summary>

* install [appimagetool](https://github.com/AppImage/appimagetool) to path
* run `ninja -C [BUILDDIR] appimage`
* your appimage should be in the build dir now
</details>

### Windows
1. make sure you have MSYS2 installed
2. boot into MSYS2 UCRT64 (important!!)
3. run `build-aux/install_deps.py`
	* this tries to install all MSYS2 and Python packages necessary for building and running
4. run `build-aux/freeze.py`
	* this will spit out an executable with some folders in `build/`
5. (optional) run `makensis build-aux/build_installer.nsi`
	* this will spit out an installer for rencher in `build/`

## credits and license

[Nicotine+](https://github.com/nicotine-plus/nicotine-plus) was used as reference for what i should do regarding pygobject and packaging
<br>
logo made by [vl1](https://vl1.neocities.org/). check him out!
<br>
this project is under the [GPL-3](https://github.com/danatationn/rencher?tab=GPL-3.0-1-ov-file)

#### © 2025 danatationn
