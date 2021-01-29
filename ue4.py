import os
import glob
from subprocess import Popen
from enum import Enum
import json
class RenderOutputFormat(object):
    JPG = "jpg"
    BMP = "bmp"
    PNG = "png"
    Video = "video"

class ImportData(object):
    pass

class StaticMeshImportData(ImportData):
    bRemoveDegenerates = True
    bBuildAdjacencyBuffer = True
    bBuildReversedIndexBuffer = False
    bGenerateLightmapUVs = False
    bOneConvexHullPerUCX = True
    bAutoGenerateCollision = False
    bCombineMeshes = False

class SkeletalMeshImportData(ImportData):
    TargetSkeleton = ""
    bUpdateSkeletonReferencePose = True
    bUseT0AsRefPose = True
    bPreserveSmoothingGroups = True
    bImportMeshesInBoneHierarchy = False
    bImportMorphTargets = True
    bKeepOverlappingVertices = True
    

class AnimSequenceImportData(ImportData):
    TargetSkeleton = ""
    bImportCustomAttribute = True
    bDeleteExistingCustomAttributeCurves = True
    bDeleteExistingNonCurveCustomAttributes = True
    bImportBoneTracks = True
    bSetMaterialDriveParameterOnCustomAttribute = True
    bRemoveRedundantKeys = False
    bDeleteExistingMorphTargetCurves = False
    bDoNotImportCurveWithZero = True
    bPreserveLocalTransform = True

class TextureImportData(ImportData):
    bInvertNormalMaps = True

class FBXImportSettings(object):

    def __init__(self):
        self.settings = dict(ImportGroups = [])
        self._groups = []

    def _add_group(self, setting_group):
        self.settings["ImportGroups"].append(setting_group)

    def addGroup(self, group_name, files_path, destination, import_setting):
        if not issubclass(import_setting.__class__, ImportData):
            print("import_setting input should be of class ImportSetting")
        setting_group = {
            "GroupName": group_name,
            "Filenames": files_path,
            "DestinationPath": destination,
            "bReplaceExisting": "true",
            "bSkipReadOnly": "true",
            "FactoryName": "FbxFactory",
            "ImportSettings": {}
        }
        raw_setting = import_setting.__dict__
        if hasattr(import_setting, "TargetSkeleton"):
            setting_group["TargetSkeleton"] = import_setting.TargetSkeleton
            raw_setting.pop("TargetSkeleton")
        setting_group["ImportSettings"][import_setting.__class__.__name__] = raw_setting

        self._add_group(setting_group)
        return setting_group

    def getGroup(self, group_name):
        for setting in self.settings["ImportGroups"]:
            if setting["GroupName"] == group_name:
                return setting

    def asJson(self, filepath=""):
        if not filepath:
            import datetime
            filepath = os.path.join(os.getenv("TMP"), "UE4CMD", "importsetting.{}.json".format(datetime.datetime.now().strftime("%d%m%Y%H%M%S")))
            try:
                os.makedirs(os.path.dirname(filepath))
            except:
                pass
        with open(filepath, "w+") as f:
            json.dump(self.settings, f, sort_keys=True, indent=4, separators=(',', ': '))
        print(filepath)
        return filepath

class NoEditorException(Exception):
    pass

class NoProjectException(Exception):
    pass

class Unreal4CMD(object):
    def __init__(self, editor="", project=""):
        self.editor = editor or os.getenv("UE4Editor", "")
        self.project = project or os.getenv("UE4Project", "")

    def getCMD(self):
        if self.editor and os.path.exists(self.editor):
            if os.path.isfile(self.editor) and os.path.basename(self.editor) == "UE4Editor-Cmd.exe":
                return self.editor
            for r in glob.glob(self.editor + "/Binaries/Win64/UE4Editor-Cmd.exe"):
                return r

    def getEditor(self):
        if self.editor and os.path.exists(self.editor):
            if os.path.isfile(self.editor) and os.path.basename(self.editor) == "UE4Editor.exe":
                return self.editor
            for r in (glob.glob(self.editor + "/Binaries/Win64/UE4Editor.exe")):
                return r

    def getProject(self):
        if self.project and os.path.exists(self.project):
            if os.path.isfile(self.project) and self.project.endswith("*.uproject"):
                return self.project
            for r in glob.glob(self.project + "/*.uproject"):
                return r

    def run_editor(
        self,
        argv= [],
        log= False,
        consolevariables= [],
        run_process_callable= Popen,
        run_process_argv= [],
        run_process_kws= {},
        custom_editor_path= "",
        custom_project_path= "",
        as_cmd= False,
        communicate = False
    ):

        editor_path = self.getEditor()
        if not editor_path:
            raise NoEditorException("No UE4 Editor Define")

        project_path = self.getProject()
        if not project_path:
            raise NoEditorException("No Project Define")

        argv.append('-ExecCmds="{}"'.format(";".join(consolevariables)))
        if log:
            try:
                if isinstance(log, str):
                    argv.append("-log")
                    argv.append('LOG="{}"'.format(log))
            except TypeError:
                argv.append(f"-log")
        if as_cmd:
            editor_path = editor_path.replace("UE4Editor", "UE4Editor-Cmd")
        p = run_process_callable(
            [editor_path, project_path, *argv],
            *run_process_argv,
            **run_process_kws,
        )
        if run_process_callable == Popen and communicate:
            p.communicate()
        return p

    def run_render(
        self,
        map_path,
        sequence_path,
        output_folder = "render",
        output_name = "Render.{frame}",
        output_format= RenderOutputFormat.PNG,
        start_frame = 0,
        end_frame = 0,
        res_x = 1920,
        rex_y = 1080,
        frame_rate = 30,
        quality = 100,
        warmup_frames = 30,
        delay_frames = 30,
        preview: bool = False
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
            f'-MovieFormat="{output_format}"',
            "-NoScreenMessage",
        ]
        if start_frame:
            cmds.append(f"-MovieStartFrame={start_frame}")
        if end_frame:
            cmds.append(f"-MovieEndFrame={end_frame}")
        return self.run_editor(cmds, as_cmd=True, log=True, communicate=True)

    def run_python(
        self,
        python_file,
        fully_initialize = False,
        log = False,
        timeout = None,
    ):
        use_cmd = True
        cmd = ["-run=pythonscript", f"-script={python_file}"]

        if fully_initialize:
            use_cmd = False
            cmd = [f'-ExecutePythonScript="{python_file}"']

        return self.run_editor(
                cmd,
                log=log,
                run_process_kws=dict(
                    encoding="utf-8",
                    timeout=timeout,
                    shell=True,
                ),
                as_cmd=use_cmd,
                communicate=True
            )

    def run_import(self, importsettings):
        cmd = ["-run=ImportAssets"]
        cmd.append('-importsettings="{}"'.format(importsettings))
        cmd.append("-replaceexisting")
        self.run_editor(cmd, as_cmd=True, communicate=True)