import logging
from thirdpartylibs.unreal_api3.ue4.unreal_global import UnrealResponse
from .setup import ue4
import pytest
import json
import os
import psutil
import re
import time
import typing
from pathlib import Path
from subprocess import CompletedProcess
from typing import cast
import pytest_datadir


class TestUnreal4:
    @pytest.fixture()
    def unreal_instance(self):
        return ue4.Unreal4()

    def setup_method(self, method):
        ue4.Unreal4.close_all_editor()
        print("setup_method      method:%s" % method.__name__)

    def teardown_method(self, method):
        print("teardown_method   method:%s" % method.__name__)

    def test_run_editor(self, unreal_instance: ue4.Unreal4):
        try:
            ue4.Unreal4().run_editor()
            ue4_instances = [
                p for p in psutil.process_iter() if re.match("UE4.+", p.name())
            ]
            assert len(ue4_instances) > 0, "Failed to launch Unreal"
        finally:
            time.sleep(1)
            ue4.Unreal4.close_all_editor()

    def test_run_python(self, unreal_instance: ue4.Unreal4, datadir: Path):
        temp_file = Path(os.getenv("TMP", "")) / "temp_file.txt"
        log_ue4 = "ue4_python_log.log"
        if temp_file.exists():
            temp_file.unlink()
        # temp_file.touch()
        command = r'a=5 \nb=10 \nc=a+b \nf=open(\"{}\",\"w+\") \nf.write(str(c)) \nf.close()'.format(temp_file.as_posix())
        p = cast(
            CompletedProcess,
            unreal_instance.run_python_cmdlet(
                command, fully_initialize=False, log=True, log_file=log_ue4
            ),
        )
        # assert p.returncode, "Failed to exec python"
        assert temp_file.exists(), f"Failed to exec python command {command}"

    def test_run_python_remote(self, unreal_instance: ue4.Unreal4, datadir: Path):
        command = 'unreal.SystemLibrary.quit_editor()'
        while not unreal_instance.get_running_unreal():
            logging.info("Wait for unreal to start...")
            time.sleep(1)
        p = cast(
            UnrealResponse,
            unreal_instance.run_python_remote(
                command
            ),
        )
        # wait for unreal to close
        time.sleep(1)

        assert unreal_instance.is_any_unreal_running(), "Failed to run remote python command"

# from CosmicShake import Factory

# def test_data():
#     new_seq = Factory.LevelSequenceFactory.create_sequence("Test Sequence", "test.usasset")

#     Factory.LevelSequenceFactory.add_sub_sequence(
#         new_seq,
#         Factory.LevelSequenceFactory.create_sequence("Test SubSequence", "testsubsequence.usasset")
#     )
#     Factory.LevelSequenceFactory.add_sub_sequence(
#         new_seq,
#         Factory.LevelSequenceFactory.create_sequence("Test SubSequence2", "testsubsequence2.usasset")
#     )
#     # Factory.LevelSequenceFactory.dump_sequence_data(subseq, "tests/test_sdump.json")
#     Factory.LevelSequenceFactory.add_character_track(
#         new_seq,
#         Factory.LevelSequenceFactory.create_character_track("Test character", "testchar.usasset", "", "", "")
#     )

#     Factory.LevelSequenceFactory.add_camera_track(
#         new_seq,
#         Factory.LevelSequenceFactory.create_camera_track("Test camera", "camear.fbx", "")
#     )

#     Factory.LevelSequenceFactory.add_mesh_track(
#         new_seq,
#         Factory.LevelSequenceFactory.create_mesh_track("Test mesh", "mesh.fbx", "")
#     )

#     # print(new_seq)
#     Factory.LevelSequenceFactory.dump_sequence_data(new_seq, "tests/test_dump_data.json")

#     assert Factory.LevelSequenceFactory.parse_json_to_sequence_data("tests/test_dump_data.json") == new_seq