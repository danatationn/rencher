import sys

from src import blp2ui
from src.gtk import RencherApplication

if __name__ == '__main__':
	blp2ui()
	app = RencherApplication()
	app.run(sys.argv)