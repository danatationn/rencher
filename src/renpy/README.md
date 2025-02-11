# my awesome spec

### terms:
* `project` - any type of Ren'Py game that can launch
* `game` - a normal project
* `mod` - a project that has been tampered with
* `codename` - the project's internal name
* `rpath` (relative path) - the top folder. this can be the same as apath
* `apath` (absolute path) - the folder which has the project's files
* `independency` - when a mod has a different Ren'Py version than the game. restricted to mods :p

### config:
1. info
    * `nickname` - whatever name you want the project to be called. if there's no nickname set it will be set as the project's folder name
2. options
    * `contained saves` - forces the savedir to `apath/game/saves` as some projects may try to save somewhere else. on by default
    * `save slots` - appends a number to the savedir like so `apath/game/saves{n}`, with `n` being your desired number. restricted to contained saves