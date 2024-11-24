from textual.app import App
from textual.widgets import Tabs

from src.tui.screens import LibraryScreen, ImportScreen, SettingsScreen


class Dossier(App):

	BINDINGS = [('q', 'quit')]
	MODES = {
		'library': LibraryScreen,
		'import': ImportScreen,
		'settings': SettingsScreen
	}
	DEFAULT_MODE = 'library'
