from pathlib import Path

from textual.widgets import OptionList
from textual.widgets.option_list import Option

from src.mods import Mod


class LibrarySidebar(OptionList):

	def __init__(self) -> None:
		super().__init__()
		self.mod_dict = {}

	def on_mount(self) -> None:
		mod_dir = Path.cwd() / 'mods'
		mod_dir.mkdir(exist_ok=True)

		mods = [Mod(rpath=mod) for mod in mod_dir.glob('*') if mod.is_dir()]

		for mod in mods:
			option_id = f'mod-{mod.name}-{mod.codename}'
			option = Option(mod.name, id=option_id)
			self.mod_dict[option_id] = mod
			self.add_option(option)

	def action_select(self) -> None:
		...
		# option = self.get_option_at_index(self.highlighted)
		# mod = self.mod_dict[option.id]
		#
		# self.notify(f'running {mod.name}...')
		# mod.run()