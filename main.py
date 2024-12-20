import sys

from src import blp2ui
blp2ui()
from src.gtk import RencherApplication

if __name__ == '__main__':
	app = RencherApplication()
	app.run(sys.argv)