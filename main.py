import sys
from src.gtk import blp2ui

def main():
	blp2ui()
	
	# ui files get loaded when the import happens
	# we want the ui that we just compiled
	from src.gtk.application import RencherApplication  # noqa: E402	
	app = RencherApplication()
	app.run(sys.argv)


if __name__ == '__main__':
	main()