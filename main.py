import sys

import src.tui.app


def start_textual() -> None:
	app = src.tui.app.Dossier()
	app.run()


def start_kirigami() -> None:
	# print("Not implemented yet!")
	start_textual()

if __name__ == '__main__':
	if sys.stdin.isatty():
		start_textual()
	else:
		start_kirigami()