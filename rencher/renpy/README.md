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

## overview of the mod class
**_DEPRECATED !!!!!_**


### game validation
we need to look at a few files to see if it can run or not:

1. do the `game/`, `renpy/` and `lib/` folders exist?
2. are there files in these folders?
3. are there any `.py` scripts in the top folder?
4. are there any `.rpa` files in `game/`?
5. are there `.py`, `.pyo`, `.pyx`, `.rpym` and `.rpymc` files in renpy/?

if so, it most likely probably CAN run
