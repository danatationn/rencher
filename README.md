# Rencher - yet another mod manager
<p align="center">
	<img src="assets/rencher-logo.png" width="400px"/>
<p/>

rencher is a ren'py game manager, made with ddlc mods in mind
<br/>
it strives to be as simple as possible, while being as beautiful as possible

[link to the trello board](https://trello.com/b/CGaqf0xx/rencher)

<br/>
<p>
	<img src="assets/Screenshot From 2025-06-28 19-05-48.png" alt="Screenshot of Rencher's UI" width="384px"/>
	<img src="assets/Screenshot From 2025-07-01 17-11-18.png" alt="Screenshot of Rencher's UI" width="384px"/>
</p>

## download!
### [windows](https://github.com/danatationn/Rencher/releases/latest/download/Rencher-Windows-Installer.exe) - [linux](https://github.com/danatationn/Rencher/releases/latest/download/Rencher-x86_64.AppImage) - ~~macos~~ (soon)

## tips
* you can turn the update toasts in the settings ^^
* you can also delete the zip files after importing. also in the settings
* if you're importing an already set up ddlc mod, then just import it normally

## possible upcoming features
- [ ] store (vndb, itch.io, the old ddmc mod list thing)
- [ ] asset viewer (unrpa + unrpyc)
- [ ] discord rpc
- [ ] more...

## compiling
> [!NOTE]
> all the steps assume you downloaded the rencher repo and your terminal is inside it
### linux
> [!WARNING]
> ubuntu 24.04 has an out of date libadwaita package. the only way to build it there is with the docker method
<details> <summary> normal </summary>

1. make sure you have `python3` installed	
2. run `build-aux/install_deps.py`
   * this tries to install all linux and python packages necessary for building and running
3. run `build-aux/freeze.py`
   * this will spit out an executable with some folders in `build/`
4. (optional) run `build-aux/appimage.py`
   * this will spit out a one file appimage, meaning you don't have to carry around the folders
5. done! retrieve your execs from `build/`

</details>
<details> <summary> docker </summary>

1. make sure you have docker set up properly
2. run these commands:
	1. `docker buildx build -t rencher-builder .`
	2. `docker create --name temp-container rencher-builder`
	3. `docker cp temp-container:/app/build/ ./output/`
	4. `docker rm temp-container`
3. done! retrieve your execs from `output/`

</details>

### windows
<details> <summary> the Only Way </summary>

1. make sure you have msys2 installed
2. boot into msys2 ucrt64 (important!!)
3. run `build-aux/install_deps.py`
	* this tries to install all msys2 and python packages necessary for building and running
4. run `build-aux/freeze.py`
	* this will spit out an executable with some folders in `build/`
5. (optional) run `makensis build-aux/build_installer.nsi`
	* this will spit out an installer for rencher in `build/`

</details>

## credits and license

[Nicotine+](https://github.com/nicotine-plus/nicotine-plus) for being made in python and using gtk . this being open source really helped me with packaging this
<br>
logo made by my good man [vl1](https://vl1.neocities.org/) . check him out!
<br>
this project is under [GNU General Public License 3.0](https://github.com/danatationn/rencher?tab=GPL-3.0-1-ov-file)

© 2025 danatationn