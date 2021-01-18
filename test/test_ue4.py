import logging
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
from .setup import ue4, UnrealRemoteResponse

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
        with unreal_instance.open():
            ue4_instances = [
                p for p in psutil.process_iter() if re.match("UE4.+", p.name())
            ]
            assert len(ue4_instances) > 0, "Failed to launch Unreal"

    def test_run_python(self, unreal_instance: ue4.Unreal4, datadir: Path):
        temp_path = Path(os.getenv("TMP", ""))
        temp_file = temp_path / "temp_file.txt"
        log_ue4 = temp_path / "ue4_python_log.log"
        if temp_file.exists():
            temp_file.unlink()
        # temp_file.touch()
        command = r'a=5 \nb=10 \nc=a+b \nf=open(\"{}\",\"w+\") \nf.write(str(c)) \nf.close()'.format(temp_file.as_posix())
        p = cast(
            CompletedProcess,
            unreal_instance.run_python_cmdlet(
                command, fully_initialize=False, log=str(log_ue4)
            ),
        )
        # assert p.returncode, "Failed to exec python"
        assert temp_file.exists(), f"Failed to exec python command {command}"

    def test_run_python_remote(self, unreal_instance: ue4.Unreal4, datadir: Path):
        with unreal_instance.open():
            max_retry = 100
            retry = 0
            unreal_instance.run_editor()
            unreal_remotes = unreal_instance.get_running_unreal_remote()
            while not unreal_remotes:
                unreal_remotes = unreal_instance.get_running_unreal_remote()
                if retry > max_retry:
                    raise Exception("Failed to Start editor")
                print("Wait for unreal to start...")
                retry +=1
                time.sleep(1)

            command = 'unreal.log(unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0,0,0), unreal.Rotator(0,0,0)))'
            p = cast(
                UnrealRemoteResponse,
                unreal_instance.run_python_remote(
                    command
                ),
            )
            # wait for result
            print(p)
            time.sleep(.1)
            assert p.success and ("StaticMeshActor" in p.output[0].output), "Failed to run remote python command"


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