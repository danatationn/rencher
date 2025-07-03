import platform
import sys
from pathlib import Path

from gi.repository import Gio

from rencher import tmp_path
from rencher.gtk import compile_data


def main() -> None:
	compile_data()
	
	# ui files get loaded when the import happens
	# we want the ui that we just compiled
	from rencher.gtk.application import RencherApplication  # noqa: E402	
	app = RencherApplication()
	
	if platform.system() == 'Windows':
		gres_path = tmp_path / 'rencher' / 'gtk' / 'res' / 'windows.resources.gresource'
	else:
		gres_path = tmp_path / 'rencher' / 'gtk' / 'res' / 'resources.gresource'
	res = Gio.resource_load(str(gres_path))	
	res._register()
	
	try:
		app.run(sys.argv)
	except KeyboardInterrupt:
		pass


if __name__ == '__main__':
	main()