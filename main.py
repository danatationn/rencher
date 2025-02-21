def main():
	import sys


	from src.gtk import blp2ui
	blp2ui()
	
	from src.gtk.application import RencherApplication
	
	app = RencherApplication()
	app.run(sys.argv)


if __name__ == '__main__':
	main()