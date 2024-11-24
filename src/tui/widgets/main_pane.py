from textual.app import ComposeResult, Widget
from textual.containers import Horizontal, Vertical, Container
from textual.scroll_view import ScrollView
from textual.widgets import Label, Button


class MainPane(ScrollView):

	def compose(self) -> ComposeResult:
		yield Container(
			Label('No mod selected', id='label-name'),
			Horizontal(
				Label('Playtime', id='label-playtime'),
				Label('Last Played', id='label-last-played'),
				Label('Size', id='label-size')
			),
			Horizontal(
				Button('Play', id='button-play'),
				Button('Options', id='button-options')
			)
		)


	def on_mount(self) -> None:
		label = self.query_one('#label-name')
		if isinstance(label, Label):
			pass

