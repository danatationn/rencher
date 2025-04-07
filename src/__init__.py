import sys
from pathlib import Path


root_path: Path = Path()

if '__compiled__' in globals():
	root_path = Path(sys.executable).parent
else:
	root_path = Path(__file__).parents[1]
