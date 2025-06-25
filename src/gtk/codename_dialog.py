from pathlib import Path

from src.renpy import Game

from gi.repository import Gtk, Adw


class RencherCodename(Adw.AlertDialog):
	def __init__(self, rpath: Path, parent: Adw.ApplicationWindow):
		super().__init__()
		self.game = Game(rpath=rpath)
	
		self.set_heading('Select Mod Executable')
		self.set_body(f'The mod "{self.game.name}" provides multiple executables.\n'
					   'Please choose the correct one below.\n'
					   '(You can change this later in settings.)')
		
		self.list_box = Gtk.ListBox()
		self.list_box.add_css_class('boxed-list')
		
		py_names = [py_path.stem for py_path in sorted(self.game.apath.glob('*.py'))]
		for name in py_names:
			row = Adw.ActionRow(title=name)
			self.list_box.append(row)
		
		self.set_extra_child(self.list_box)
	
		self.add_response('ok', 'OK')
		self.set_default_response('ok')
		# self.set_response_appearance('ok', Adw.ResponseAppearance.SUGGESTED)
	
		self.connect('response', self.on_response)
		
	def on_response(self, dialog, response):
		codename = self.list_box.get_selected_row().get_title()
		self.game.config['info']['codename'] = codename
		self.game.config.write()