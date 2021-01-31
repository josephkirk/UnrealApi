# UNREALAPI

unrealapi is a pure python library to communicate with unreal for commandline task such as import asset. this branch support python 2+

**usage:**
```python
from unrealapi import ue4
ue4cmd = ue4.Unreal4CMD()

# if editorpath or projectpath is not defined, it is taken from environment variable "UE4Editor" and "UE4Project"
ue4.cmd.run_editor(editor=editorpath, project=projectpath)
```

*--see tests file for detail example on how to use--*