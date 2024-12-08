from textual.app import ComposeResult, Screen
from textual.widgets import OptionList, Footer

from src.tui.widgets.entry import Entry


class DossierScreen(Screen):

	BINDINGS = [
		('f1', 'show_library', 'Library'),
		('f2', 'show_import', 'Import'),
		('f3', 'show_settings', 'Settings')
	]

	def compose(self) -> ComposeResult:
		yield Footer(show_command_palette=False)

	def action_show_library(self) -> None:
		self.app.switch_mode('library')
	def action_show_import(self) -> None:
		self.app.switch_mode('import')
	def action_show_settings(self) -> None:
		self.app.switch_mode('settings')



class LibraryScreen(DossierScreen):
	CSS_PATH = 'tcss/entry.tcss'

	def compose(self) -> ComposeResult:
		yield from super().compose()
		yield Entry()

class ImportScreen(DossierScreen):
	def compose(self) -> ComposeResult:
		yield from super().compose()
		yield OptionList(
			'hi',
			'i',
			'am',
			'the',
			'import',
			'screen'
		)


class SettingsScreen(DossierScreen):
	def compose(self) -> ComposeResult:
		yield from super().compose()
		yield OptionList(
			'Settings'
		)