import sys
from pathlib import Path

outerpath = str(Path(__file__).parent.parent.parent)
if outerpath not in sys.path:
    print(f'OuterPath: {outerpath}')
    sys.path.append(outerpath)

from unreal_api3 import ue4
