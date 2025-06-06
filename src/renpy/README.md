# my awesome spec

### terms:
* `game` - a ren'py game
* `mod` - a game that has been tampered with (notably having its scripts.rpa modified)
* `codename` - the project name
* `rpath` (relative path) - the top folder. this can be the same as apath
* `apath` (absolute path) - the folder which has the game's files

### config:
1. info
    * `nickname` - whatever name you want the project to be called. if there's no nickname set it will be set as the project's folder name
2. options
    * `contained saves` - forces the savedir to `apath/game/saves` as some projects may try to save somewhere else. on by default
    * `save slots` - appends a number to the savedir like so `apath/game/saves{n}`, with `n` being your desired number. restricted to contained saves