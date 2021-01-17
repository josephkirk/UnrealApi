import json
from .Data import *

class LevelSequenceFactory():
    @staticmethod
    def create_sequence(name, sourceasset, cinerootsourcefbx="", start=0, end=1, tracks=None, subsequences={}):
        # subsequences = { k:v for k,v in subsequences.items() if isinstance(v, LevelSequenceStruct) }
        newseqdata = LevelSequenceStruct(
            name = name,
            sourceasset = sourceasset,
            cinerootsourcefbx = cinerootsourcefbx,
            start = start,
            end = end,
            tracks = LevelSequenceTrack(characters={}, additionalmeshes={}, cameras={}),
            subsequences = subsequences
        )
        return newseqdata

    @staticmethod
    def add_sub_sequence(sequence_object, subsequence_object):
        if isinstance(subsequence_object, LevelSequenceStruct):
            sequence_object.subsequences[subsequence_object.name] = subsequence_object
            return True
        return False

    @staticmethod
    def create_character_track(name, sourcefbx, uasset, skeletaluasset, mayarig):
        return LevelSequenceCharacter(name=name, sourcefbx=sourcefbx, uasset=uasset, skeletaluasset=skeletaluasset, mayarig=mayarig)

    @staticmethod
    def add_character_track(sequence_object, character_track):
        if isinstance(character_track, LevelSequenceCharacter):
            sequence_object.tracks.characters[character_track.name] = character_track
            return True
        return False

    @staticmethod
    def create_mesh_track(name, sourcefbx, uasset):
        return UnrealAsset(name=name, sourcefbx=sourcefbx, uasset=uasset)

    @staticmethod
    def add_mesh_track(sequence_object, mesh_track):
        if isinstance(mesh_track, UnrealAsset):
            sequence_object.tracks.additionalmeshes[mesh_track.name] = mesh_track
            return True
        return False

    @staticmethod
    def create_camera_track(name, sourcefbx, mayarig):
        return LevelSequenceCamera(name=name, sourcefbx=sourcefbx, mayarig=mayarig)

    @staticmethod
    def add_camera_track(sequence_object, camera_track):
        if isinstance(camera_track, LevelSequenceCamera):
            sequence_object.tracks.cameras[camera_track.name] = camera_track
            return True
        return False

    @staticmethod
    def parse_json_to_sequence_data(json_path):
        with open(json_path, 'r') as f:
            return Box(json.load(f))

    @staticmethod
    def dump_sequence_data(sequence_object, json_path):
        if not isinstance(sequence_object, LevelSequenceStruct):
            return False
        sequence_object.to_json(json_path, indent=4, sort_keys=True)
        return True