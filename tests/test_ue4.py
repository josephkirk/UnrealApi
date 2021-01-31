#!Python3
import os, sys
import re

import pytest
import psutil
from pathlib import Path


@pytest.fixture(scope="session")
def datapath():
    return Path(__file__).parent / Path(__file__).stem

@pytest.fixture(scope="session")
def editorpath():
    return r"D:\Epic\UE_4.25\Engine"

@pytest.fixture(scope="session")
def temppath():
    p = Path(os.getenv("TMP")) / Path(__file__).stem
    if not p.exists():
        os.makedirs(p)
    return p

@pytest.fixture(scope="session")
def projectpath(datapath):
    return str(datapath / "TemplateProject")

class TestUE4API:
    @pytest.fixture()
    def ue4(self):
        from unrealapi import ue4
        return ue4

    @pytest.fixture()
    def ue4cmd(self, ue4, editorpath, projectpath):

        return ue4.Unreal4CMD(
                            editor = editorpath,
                            project = projectpath
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

    @pytest.mark.dependency()
    def test_run_editor(self, ue4cmd):
        ue4cmd.run_editor()
        ue4_instances = [
                p for p in psutil.process_iter() if re.match("UE4.+", p.name())
            ]
        assert len(ue4_instances) > 0, "Failed to launch Unreal"

    @pytest.mark.dependency(depends=["TestUE4API::test_run_editor"])
    def test_run_import_animation(self, ue4, ue4cmd, datapath, projectpath):
        expected_file = Path(projectpath) / "Content/Animations/Deaths_Shoulder_Crawl.uasset"
        try:
            if expected_file.exists():
                expected_file.unlink()
            importsetting= ue4.FBXImportSettings()
            animimportsetting = ue4.AnimSequenceImportData()
            animimportsetting.TargetSkeleton = "/Game/AnimStarterPack/UE4_Mannequin/Mesh/UE4_Mannequin_Skeleton"
            importsetting.addGroup("Animation", [str(datapath / "Deaths_Shoulder_Crawl.FBX")], "/Game/Animations/", animimportsetting)
            result = ue4cmd.run_import(importsetting.asJson())
            import time
            time.sleep(1)
            assert expected_file.exists(), "Failed To import Animation Asset"
        finally:
            expected_file.unlink()

    @pytest.mark.dependency(depends=["TestUE4API::test_run_editor"])
    def test_run_reimport_animation(self, ue4, ue4cmd, datapath, temppath, projectpath):
        import shutil
        expected_file = Path(projectpath) / "Content/AnimStarterPack/Fire_Shotgun_Hip.uasset"
        tempfile = temppath / expected_file.name
        if tempfile.exists():
            tempfile.unlink()
        shutil.copyfile(str(expected_file), str(tempfile))
        shutil.copystat(str(expected_file), str(tempfile))
        try:
            if not expected_file.exists():
                assert False, "Missing test file for reimport"
            file_modtime = expected_file.stat().st_mtime
            importsetting= ue4.FBXImportSettings()
            animimportsetting = ue4.AnimSequenceImportData()
            animimportsetting.TargetSkeleton = "/Game/AnimStarterPack/UE4_Mannequin/Mesh/UE4_Mannequin_Skeleton"
            importsetting.addGroup("Animation", [str(datapath / "Fire_Shotgun_Hip.FBX")], "/Game/AnimStarterPack/", animimportsetting, is_reimport=True)
            result = ue4cmd.run_import(importsetting.asJson())
            import time
            time.sleep(1)
            assert file_modtime != expected_file.stat().st_mtime, "Failed To reimport Animation Asset"
        finally:
            expected_file.unlink()
            shutil.copyfile(str(tempfile), str(expected_file))
            shutil.copystat(str(tempfile), str(expected_file))