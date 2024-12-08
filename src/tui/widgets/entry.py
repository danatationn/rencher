from textual.app import ComposeResult, Widget
from textual.containers import Grid, Container, Horizontal, Vertical
from textual.widgets import Label, Button


class Entry(Container):

	CSS_PATH = '../tcss/entry.tcss'

	def compose(self) -> ComposeResult:
		yield Horizontal(
			Label('Mod Name', id='label-name'),
			Label('☆', id='button-star')
		)

		yield Horizontal(
			Vertical(
				Label('🕓 Playtime', id='label-playtime'),
				Label('🗓️  Last Played', id='label-last-played'),
				Label('💾 Size', id='label-size'),
				Label('📦 Version', id='label-version')
			),
			Vertical(
				Label('🖼️  Screenshots', id='label-screenshots')
				# screenshot widget
			)
		)

		yield Horizontal(
			Button('▶️  Play', id='button-play', variant='success'),
			Button('⚙️  Options', id='button-options', variant='primary')
		)


	def on_mount(self) -> None:
		...