#!Python3
import os, sys
import re

import pytest
import psutil
from pathlib import Path

def get_editor():
    return r"D:\Epic\UE_4.25\Engine"

def get_project():
    return r"D:\unreal\PythonProject425"

@pytest.fixture(scope="session")
def datapath():
    return Path(__file__).parent / Path(__file__).stem

class TestUE4API:
    @pytest.fixture()
    def ue4(self):
        from unrealcmd_api import ue4
        return ue4

    @pytest.fixture()
    def ue4cmd(self, ue4):
        
        
        return ue4.Unreal4CMD(
                            editor = get_editor(),
                            project = get_project()
        )

    def setup_method(self, method):
        print("teardown_method   method:%s" % method.__name__)
        ue4_instances = (
                p for p in psutil.process_iter() if re.match("UE4.+", p.name())
        )
        for ue4_instance in ue4_instances:
            ue4_instance.kill()

    def teardown_method(self, method):
        print("teardown_method   method:%s" % method.__name__)
        ue4_instances = (
                p for p in psutil.process_iter() if re.match("UE4.+", p.name())
        )
        for ue4_instance in ue4_instances:
            ue4_instance.kill()


    def test_run_editor(self, ue4cmd):
        ue4cmd.run_editor()
        ue4_instances = [
                p for p in psutil.process_iter() if re.match("UE4.+", p.name())
            ]
        assert len(ue4_instances) > 0, "Failed to launch Unreal"

    def test_run_import_animation(self, ue4, ue4cmd, datapath):
        importsetting= ue4.FBXImportSettings()
        animimportsetting = ue4.AnimSequenceImportData()
        animimportsetting.TargetSkeleton = "/Game/Deaths/Character/Mesh/UE4_Mannequin_Skeleton"

        importsetting.addGroup("Animation", [str(datapath / "Deaths_Shoulder_Crawl.FBX")], "/Game/Animations/", animimportsetting)
        ue4cmd.run_import(importsetting.asJson())
        assert False