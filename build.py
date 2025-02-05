def main():
	import PyInstaller.__main__
	from pathlib import Path

	setup_path = Path(__file__).parent.absolute()
	main_path = setup_path / 'main.py'


	PyInstaller.__main__.run([
		str(main_path),
		'--onefile'
	])
	
	
if __name__ == '__main__':
	main()