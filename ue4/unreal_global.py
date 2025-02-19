# utf-8
# python 3.9
# Nguyen Phi Hung @ 2021
# nguyenphihung.tech@outlook.com
from __future__ import annotations

import os
import sys
import subprocess
from subprocess import CompletedProcess, Popen
import time
from typing import Any, Union, Sequence, Callable, cast, Optional, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field, InitVar
from pathlib import Path
from yaml import CLoader, load, dump, CDumper
from box import Box
from enum import Enum, auto

from .remote_execution import RemoteExecution, RemoteExecutionConfig
from importlib_resources import files
from .utils import close_all_app, is_any_running, logging

# Error Class
class Unreal4ConfigError(ValueError):
    pass


# Enum
# Struct
global_remote = RemoteExecution()
global_remote.start()


class RenderOutputFormat(Enum):
    JPG = auto()
    BMP = auto()
    PNG = auto()
    Video = auto()


@dataclass
class UnrealRemoteOutput:
    type: str = field(default_factory=str)
    output: str = field(default_factory=str)


UnrealRemoteOutputs = list[UnrealRemoteOutput]


@dataclass
class UnrealRemoteResponse:
    """Unreal Response from remote request"""

    success: str = field(default_factory=str)
    result: str = field(default_factory=str)
    command: str = field(default_factory=str)
    output: InitVar[UnrealRemoteOutputs] = []

    def __post_init__(self, output):
        self.output = [UnrealRemoteOutput(**o) for o in output]


@dataclass
class UnrealRemoteInfo:
    user: str
    machine: str
    engine_version: str
    engine_root: str
    project_root: str
    project_name: str
    node_id: str


@dataclass
class AssetImportData:
    fbx_file_path: str = field(default_factory=str)
    game_path: str = field(default_factory=str)
    skeleton_game_path: str = field(default_factory=str)
    skeletal_mesh: bool = field(default=False)
    animation: bool = field(default=False)
    import_mesh: bool = field(default=True)
    lods: bool = field(default=True)


@dataclass
class AssetImportProperties:
    advanced_ui_import: bool = field(default=False)
    replace_existing: bool = field(default=True)
    auto_compute_lod_distances: bool = field(default=False)
    import_materials: bool = field(default=False)
    import_textures: bool = field(default=True)
    generate_lightmap_uv: bool = field(default=False)
    import_object_name_as_root: bool = field(default=False)
    lod_distance0: float = field(default=1.0)
    lod_number: int = field(default=0)


# CoreClass


class Unreal4Config:
    remote_config = RemoteExecutionConfig()
    config_path = os.getenv("UE4_REMOTE_CONFIG", "") or "Unreal4Config.yml"

    def __init__(self, unreal_path: str, project_path: str):
        self.ue4editor = str(Path(unreal_path).resolve().as_posix())
        self.project_file = str(Path(project_path).resolve().as_posix())
        if not self.validate_editor(self.ue4editor):
            raise Unreal4ConfigError(
                f"{unreal_path} is not valid. Unreal path must point to UE4Editor.exe"
            )
        if not self.validate_project(self.project_file ):
            raise Unreal4ConfigError(
                f"{project_path} is not valid. Project file must be a uproject file."
            )

    @classmethod
    def default(cls):
        return cls(
            unreal_path=os.getenv("UE4Editor", ""),
            project_path=os.getenv("UE4Project", "")
        )

    @staticmethod
    def validate_editor(unreal_path: str) -> bool:
        _unreal_path = Path(unreal_path)
        return _unreal_path.is_file() and any(
            _unreal_path.name == editor_name
            for editor_name in ["UE4Editor.exe", "UE4Editor-Cmd.exe"]
        )

    @staticmethod
    def validate_project(project_path: str) -> bool:
        _project_path = Path(project_path)
        return _project_path.is_file() and _project_path.suffix == ".uproject"

    @classmethod
    def get_config(cls, config_path: str = config_path) -> Unreal4Config:
        config_file = Path(config_path)
        if not (config_path and config_file.exists()):
            return cls.default()

        config = load(config_file.read_text(encoding="utf-8"), Loader=CLoader)
        if hasattr(config, "get") and config.get("Unreal"):
            return cls(**config.get("Unreal"))
        else:
            raise Unreal4ConfigError(
                f"{config_path} is not valid! Config must contain Unreal section with valid unreal_path and project_path! "
            )

    @staticmethod
    def get_remote_config(remote_config=remote_config):
        return remote_config


class Unreal4:
    # Global Remote Exec Instance

    ## properties

    ## class
    class PythonExecMode(Enum):
        REMOTE = auto()
        CMDLET = auto()

    # private

    def __init__(self, config: Unreal4Config = None):
        self._config = config

    @property
    def config(self):
        if not self._config:
            self._config = Unreal4Config.get_config()
        return self._config

    # public
    @contextmanager
    def open(self, wait_before_close: int = 1) -> Iterator[Unreal4]:
        self.close_all_editor()
        try:
            self.run_editor()
            yield self
        finally:
            time.sleep(wait_before_close)
            self.close_all_editor()

    ## getter
    @staticmethod
    def get_unreal_remote(
        remote_exec: RemoteExecution = global_remote,
    ) -> RemoteExecution:
        return remote_exec

    @staticmethod
    def get_running_unreal_remote(
        remote_exec: RemoteExecution = global_remote,
    ) -> list[UnrealRemoteInfo]:
        return [UnrealRemoteInfo(**n) for n in remote_exec.remote_nodes]

    @staticmethod
    def is_any_unreal_running() -> bool:
        return is_any_running("UE4.+")

    @staticmethod
    def close_all_editor():
        close_all_app("UE4.+")

    def run_editor(
        self,
        argv: list[str] = [],
        log: Union[bool, str] = False,
        consolevariables: list[str] = [],
        run_process_callable: Callable = Popen,
        run_process_argv: Sequence[str] = [],
        run_process_kws: dict[str, Any] = {},
        custom_editor_path: str = "",
        custom_project_path: str = "",
        as_cmd: bool = False
    ) -> Union[Popen, CompletedProcess, Any]:
        argv.append('-ExecCmds="{}"'.format(";".join(consolevariables)))
        if log:
            try:
                log_file = Path(cast(str, log))
                if log_file.exists():
                    argv.append(f"-log")
                    argv.append(f'LOG="{str(log_file.as_posix())}"')
            except TypeError:
                argv.append(f"-log")
        editor_path = (
            custom_editor_path
            if Unreal4Config.validate_editor(custom_editor_path)
            else str(self.config.ue4editor)
        )
        project_path = (
            custom_project_path
            if Unreal4Config.validate_project(custom_project_path)
            else str(self.config.project_file)
        )
        if as_cmd:
            editor_path = editor_path.replace("UE4Editor", "UE4Editor-Cmd")
        logging.info(f"Exec {editor_path} {project_path} {argv}")
        return run_process_callable(
            [editor_path, project_path, *argv],
            *run_process_argv,
            **run_process_kws,
        )

    def run_render(
        self,
        map_path: str,
        sequence_path: str,
        output_folder: str = "render",
        output_name: str = "Render.{frame}",
        output_format: RenderOutputFormat = RenderOutputFormat.PNG,
        start_frame: int = 0,
        end_frame: int = 0,
        res_x: int = 1920,
        rex_y: int = 1080,
        frame_rate: int = 30,
        quality: int = 100,
        warmup_frames: int = 30,
        delay_frames: int = 30,
        preview: bool = False,
    ):
        cmds = [
            map_path,
            "-game",
            '-MovieSceneCaptureType="/Script/MovieSceneCapture.AutomatedLevelSequenceCapture"',
            f'-LevelSequence="{sequence_path}"',
            "-noloadingscreen ",
            f"-ResX={res_x}",
            f"-ResY={rex_y}",
            "-ForceRes",
            "-NoVSync" if preview else "-VSync",
            f"-MovieFrameRate={frame_rate}",
            "-NoTextureStreaming",
            "-MovieCinematicMode=Yes",
            f"-MovieWarmUpFrames={warmup_frames}",
            f"-MovieDelayBeforeWarmUp={delay_frames}",
            f"-MovieQuality={quality}",
            f'-MovieFolder="{output_folder}"',
            f'-MovieName="{output_name}"',
            f'-MovieFormat="{output_format.name}"',
            "-NoScreenMessage",
        ]
        if start_frame:
            cmds.append(f"-MovieStartFrame={start_frame}")
        if end_frame:
            cmds.append(f"-MovieEndFrame={end_frame}")

    def run_python(
        self,
        python_script: str,
        exec_mode: PythonExecMode = PythonExecMode.CMDLET,
        *args,
        **kws,
    ) -> Union[CompletedProcess, UnrealRemoteResponse]:
        return Unreal4.PythonExecModes[exec_mode](python_script, *args, **kws)

    def run_python_cmdlet(
        self,
        python_file: str,
        fully_initialize: bool = False,
        log: Union[bool, str] = False,
        timeout: int = None,
    ) -> CompletedProcess:
        use_cmd = True
        cmd = ["-run=pythonscript", f"-script={python_file}"]

        if fully_initialize:
            use_cmd = False
            cmd = [f'-ExecutePythonScript="{python_file}"']

        return cast(
            CompletedProcess,
            self.run_editor(
                cmd,
                log=log,
                run_process_callable=subprocess.run,
                run_process_kws=dict(
                    encoding="utf-8",
                    timeout=timeout,
                    shell=True,
                    check=False,
                    capture_output=False,
                ),
                as_cmd=use_cmd
            ),
        )

    @staticmethod
    def run_python_remote(
        commands: str,
        remote_exec: RemoteExecution = global_remote,
        failed_connection_attempts: int = 0,
        max_failed_connection_attempts: int = 50,
    ) -> UnrealRemoteResponse:
        """
        This function finds the open unreal editor with remote connection enabled, and sends it python commands.

        :param object remote_exec: A RemoteExecution instance.
        :param str commands: A formatted string of python commands that will be run by the engine.
        :param int failed_connection_attempts: A counter that keeps track of how many times an editor connection attempt
        was made.
        """
        # wait a tenth of a second before attempting to connect
        time.sleep(0.1)
        try:
            # try to connect to an editor
            for node in remote_exec.remote_nodes:
                remote_exec.open_command_connection(node.get("node_id"))

            # if a connection is made
            if remote_exec.has_command_connection():
                # run the import commands and save the response in the global unreal_response variable
                return UnrealRemoteResponse(
                    **remote_exec.run_command(commands, unattended=False)
                )

            # otherwise make an other attempt to connect to the engine
            else:
                if failed_connection_attempts < max_failed_connection_attempts:
                    return Unreal4.run_python_remote(
                        commands, remote_exec, failed_connection_attempts + 1
                    )
                else:
                    remote_exec.stop()
        # shutdown the connection
        finally:
            remote_exec.stop()
        return UnrealRemoteResponse("", "Failed To Connect To Unreal")

    def import_asset(
        self,
        asset_data: AssetImportData,
        properties: AssetImportProperties,
        as_remote: bool = False,
        remote_exec: RemoteExecution = global_remote,
    ) -> bool:
        """
        This function imports an asset to unreal based on the asset data in the provided dictionary.

        :param dict asset_data: A dictionary of import parameters.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        """
        # start a connection to the engine that lets you send python strings
        import_command = "\n".join(
            [
                f"import_task = unreal.AssetImportTask()",
                f'import_task.filename = r"{asset_data.fbx_file_path}"',
                f'import_task.destination_path = r"{asset_data.game_path}"',
                f"import_task.automated = {not properties.advanced_ui_import}",
                f"import_task.replace_existing = {not properties.replace_existing}",
                f"options = unreal.FbxImportUI()",
                f"options.auto_compute_lod_distances = {not properties.auto_compute_lod_distances}",
                f"options.lod_number = {not properties.lod_number}",
                f"options.import_as_skeletal = {bool(asset_data.skeletal_mesh)}",
                f"options.import_animations = {bool(asset_data.animation)}",
                f"options.import_materials = {properties.import_materials}",
                f"options.import_textures = {properties.import_textures}",
                f"options.import_mesh = {bool(asset_data.import_mesh)}",
                f"options.static_mesh_import_data.generate_lightmap_u_vs = {not properties.generate_lightmap_uv}",
                f"options.lod_distance0 = {not properties.lod_distance0}",
                # if this is a skeletal mesh import
                f"if {bool(asset_data.skeletal_mesh)}:",
                f"\toptions.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH",
                f"\toptions.skeletal_mesh_import_data.import_mesh_lo_ds = {asset_data.lods}",
                # if this is an static mesh import
                f"if {not bool(asset_data.skeletal_mesh)}:",
                f"\toptions.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH",
                f"\toptions.static_mesh_import_data.import_mesh_lo_ds = {asset_data.lods}",
                # if this is an animation import
                f"if {bool(asset_data.animation)}:",
                f'\tskeleton_asset = unreal.load_asset(r"{asset_data.skeleton_game_path}")',
                # if a skeleton can be loaded from the provided path
                f"\tif skeleton_asset:",
                f'\t\toptions.set_editor_property("skeleton", skeleton_asset)',
                f'\t\toptions.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_ANIMATION)',
                f'\t\toptions.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)',
                f'\t\toptions.anim_sequence_import_data.set_editor_property("preserve_local_transform", True)',
                f"\telse:",
                f'\t\traise RuntimeError("Unreal could not find a skeleton here: {asset_data.skeleton_game_path}")',
                # assign the options object to the import task and import the asset
                f"import_task.options = options",
                f"unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([import_task])",
                # check for a that the game asset imported correctly if the import object name as is False
                f"if {not properties.import_object_name_as_root}:",
                f'\tgame_asset = unreal.load_asset(r"{asset_data.game_path}")',
                f"\tif not game_asset:",
                f'\t\traise RuntimeError("Multiple roots are found in the bone hierarchy. Unreal will only support a single root bone.")',
            ]
        )

        # send over the python code as a string
        if as_remote:
            unreal_response = Unreal4.run_python_remote(
                import_command,
                remote_exec,
            )

            # if there is an error report it
            if unreal_response:
                if unreal_response.result != "None":
                    print(unreal_response.result)
                    return False
            return True
        else:
            p = self.run_python_cmdlet(import_command)
            return not bool(p.returncode)

    def asset_exists_remote(
        self, asset_path: str, as_remote: bool=False, remote_exec: RemoteExecution = global_remote
    ) -> bool:
        """
        This function checks to see if an asset exist in unreal.

        :param str asset_path: The game path to the unreal asset.
        :return bool: Whether or not the asset exists.
        """
        # start a connection to the engine that lets you send python strings
        # send over the python code as a string
        command = "\n".join(
            [
                f'game_asset = unreal.load_asset(r"{asset_path}")',
                f"if game_asset:",
                f"\tpass",
                f"else:",
                f'\traise RuntimeError("Asset not found")',
            ]
        )
        unreal_response = Unreal4.run_python_remote(
            command,
            remote_exec,
        )
        if as_remote:
            unreal_response = Unreal4.run_python_remote(
                command,
                remote_exec,
            )

            # if there is an error report it
            if unreal_response:
                if unreal_response.result != "None":
                    print(unreal_response.result)
                    return False
            return True
        else:
            p = self.run_python_cmdlet(command)
            return not bool(p.returncode)
        return bool(unreal_response.success)

    PythonExecModes = {
        PythonExecMode.REMOTE: run_python_remote,
        PythonExecMode.CMDLET: run_python_cmdlet,
    }