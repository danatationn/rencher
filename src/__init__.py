import sys
from pathlib import Path


root_path: Path = Path()
tmp_path: Path = Path(__file__).parents[1]

if '__compiled__' in globals():
	# root_path = Path(sys.modules["__main__"].__file__)
	root_path = Path(sys.argv[0]).parent
else:
	root_path = Path(__file__).parents[1]
