## overview of the game class

ren'py games are mostly made out of the following:
* python script that launches ren'py, named after the project
* game/ folder holding the game data (.rp files, images, translations, sounds)
* renpy/ folder with engine data (aka NERD SHIT!!)
* lib/ folder containing .exes and python libraries
* MORE !

the apath (absolute path) is the directory where all da files are 😁
<br>
and rpath is the top most directory . it may not have the game files . it may be apath . We dk

the way apath is found is by looking for .rpa/.rpy/.rpyc files
<br>
when files are found, it selects the least nested file and then returns the directory outside it twice (game > The actual game)

codenames are the project names . they're taken from the python script

getting the version is a really stupid process and the docstring should be enough to understand it

the config files are really cool and it self regenerates and shi
<br>
i'm proud of them 🥹

### game validation
we need to look at a few files to see if it can run or not:

1. do the `game/`, `renpy/` and `lib/` folders exist?
2. are there files in these folders?
3. are there any `.py` scripts in the top folder?
4. are there any `.rpa` files in `game/`?
5. are there `.py`, `.pyo`, `.pyx`, `.rpym` and `.rpymc` files in renpy/?

if so, it most likely probably CAN run


## configs
some things to clarify first:
* skip_splash_scr - Skips the splash screen at game startup
* skip_main_menu - Skips the main menu at game startup
* forced_save_dir - Forces the game to use [APATH]/game/saves as the save directory
* bool+ - kind of like a trinary switch . when left blank it falls back to the rencher config value

### Rencher configs
stores app settings
<br>
this is what it has in store:

| Key      | Option           | Default value | Expected type | Comments                                                                                                                              |
|----------|------------------|---------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------|
| settings | data_dir         | ""            | str           | Defaults depend on the OS. Linux uses `$HOME/.local/share/rencher/` and Windows uses `%localappdata%\Rencher\`                        |
| settings | suppress_updates | false         | bool          | By default, Rencher checks the latest version on startup and displays a toast if you're out of date. You can, obviously, disable this |
| settings | delete_on_import | false         | bool          | Deletes archives/folders when successfully importing a game. Was on by default but it kept pissing me off during testing              |
| settings | skip_splash_scr  | false         | bool          |                                                                                                                                       |
| settings | skip_main_menu   | false         | bool          |                                                                                                                                       |
| settings | forced_save_dir  | false         | bool          |                                                                                                                                       |

### game configs
they track stuff! heavily inspired by the Doki Doki Mod Manager config files
<br>
this is what they track:

| Key         | Option                    | Default value                           | Expected type | Comments                                                                                                                      |
|-------------|---------------------------|-----------------------------------------|---------------|-------------------------------------------------------------------------------------------------------------------------------|
| info        | nickname                  | The name of the game                    | str           |                                                                                                                               |
| info        | last_played               | 0.0                                     | float         |                                                                                                                               |
| info        | playtime                  | 0.0                                     | float         |                                                                                                                               |
| info        | added_on                  | Current epoch time                      | float         |                                                                                                                               |
| info        | codename                  | Name of the preferred Python executable | str           | Left blank if it can't be determined                                                                                          |
| options     | skip_splash_scr           | ""                                      | bool+         |                                                                                                                               |
| options     | skip_main_menu            | ""                                      | bool+         |                                                                                                                               |
| options     | forced_save_dir           | ""                                      | bool+         |                                                                                                                               |
| options     | save_slot                 | 1                                       | int           | Appends numbers to the "forced save directory" as makeshift save slots. Requires `forced_save_dir` to be on                   |
| overwritten | [everything from options] | N/A                                     | ermmmmmmmmm   | Gets made at runtime. Isn't actually in the config file. Combines the default options from the Rencher config and game config |


## paths
does some fucky shit with files for my amusement
<br>
kind of obvious what everything does

shoutout to @lru_cache