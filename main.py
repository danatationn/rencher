import sys
import os

from src import tmp_path
tmp = str(tmp_path)

if '__compiled__' in globals():
	gtk_path = tmp_path / 'libgtk-4-1.dll'
	print(gtk_path.exists())

	os.environ['PATH'] = os.pathsep.join([tmp, os.environ.get('PATH', '')])	
	os.add_dll_directory(tmp)
	
from src.gtk import blp2ui  # noqa: E402
blp2ui()

from src.gtk.application import RencherApplication  # noqa: E402

app = RencherApplication()
app.run(sys.argv)


