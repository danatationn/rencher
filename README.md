# Rencher - a Ren'Py game manager

### why?
this was originally a ddlc mod manager because all of them suck. 

however i thought it would've been better if it supported all ren'py games

it was originally named Doki Doki Mod Swapper, then Dossier and now Rencher (Ren'py + Launcher)! 😁😁

### when?
idfk i've been trying to make this for like a year now 😭

back when it was named dossier, i tried adding way too many features and it just slowed dev down to a halt

also i didn't know anything about how to make your code good so,,

here's [a link to the trello board](https://trello.com/b/CGaqf0xx/rencher) lmao

### promised features
* multiple save directories (i think i'll call them slots or something dumb like that)
* a nice looking ui :) (most likely will be made using gtk)
* ~~symlinking base assets for mods (for unix only)~~ No
* fully portable
* other

### future additions maybe
* asset unpacking and maybe editing too
* ddlc mod list integration
* vndb integration
* other

## running/compiling
**!! you're on your own here !!**

first of all, this is **NOT** production ready whatsoever

you will encounter lots of weird errors that only i know how to circumvent, and it will generally be a pain trying to use this app, at its current stage

second of all, right now this is tailored to linux specifically

while i will be forced to make this work on windows too, there are a lot of hiccups that happen on windows

for example, you cannot compile the .blp files used for the ui because [blueprint-compiler](https://jwestman.pages.gitlab.gnome.org/blueprint-compiler/) is [linux-only](https://patorjk.com/software/taag/#p=display&f=Doom&t=lol!!!!) (for some fucking reason)

**if you really want to run it right now...**

1. install [blueprint-compiler](https://jwestman.pages.gitlab.gnome.org/blueprint-compiler/) (linux-only right now!)
2. install dependencies from `pyproject.toml`
3. create the `games` and `mods` directories 
4. run `main.py`
5. try to avoid bugs

note that **if you really want to build it right now** then you can run the `build.py` file

## license

[GNU General Public License 3.0](https://github.com/danatationn/rencher?tab=GPL-3.0-1-ov-file) © 2007  Free Software Foundation