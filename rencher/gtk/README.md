### this provides a quick rundown on how all the gtk things work

## application
before application is even imported these two steps happen:
1. compiles .ui and .gresource files
2. registers the .gresource file

then it creates args, sets up the logging and checks to see if there's a new version of rencher
<br>
and now it displays the window

## window
the window is a bit complex
<br>
it consists of:
* the sidebar (where all the game buttons are)
* the headerbar
* and the views:
	* no games (status page asking you to import something. no sidebar)
    * yes games (status page asking you to click on a game. yes sidebar)
    * selected (status page showing game info. yes sidebar)

whenever you click on a game, it emits the signal to update the game view by switching `self.current_game.game` for a new game
it also binds all the info rows accordingly

TODO talk about the processes here

## game_item
a gobject.object specifically made just for the selected view
<br>
it holds the info of a game 🤷

TODO write more here

## _library
to display the buttons it has to jump some hoops

first it gets all the games you have
<br>
then they get compared to the games you already have on screen
<br>
these are sorted by:
* added games
* removed games
* changed games (everything that isn't new or deleted)

if a game is added it adds the button to the sidebar
<br>
if it's removed it removes it
<br>
~~and if it's modified it switches the game from the button to the updated one~~
<br>
what do you mean that's not what it does

oh yes. that's the job of the

## filemonitor
originally i wanted this to be native to gtk and use gio.file monitors but they are so fucking slow
<br>
seriously. do not use gio.file use literally anything else
<br>
just globbing for files takes an eternity

when initialised, it will start observing the config file and the data directory
<br>
if the config file gets changed, the filemonitor will assume that the data directory got changed too, and it updates it to the new one

i haven't figured all the code currently i will need to think long and hard on how to implement all this

TODO right a book about this when you finish it

## TODO the rest