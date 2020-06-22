from enum import IntFlag

import numpy as np

from ....byte_io_mdl import ByteIO
from ...new_shared.base import Base


# noinspection SpellCheckingInspection
class AnimDescFlags(IntFlag):
    LOOPING = 0x0001
    SNAP = 0x0002
    DELTA = 0x0004
    AUTOPLAY = 0x0008
    POST = 0x0010
    ALLZEROS = 0x0020
    FRAMEANIM = 0x0040
    CYCLEPOSE = 0x0080
    REALTIME = 0x0100
    LOCAL = 0x0200
    HIDDEN = 0x0400
    OVERRIDE = 0x0800
    ACTIVITY = 0x1000
    EVENT = 0x2000
    WORLD = 0x4000
    NOFORCELOOP = 0x8000
    EVENT_CLIENT = 0x10000


class AnimDesc(Base):

    def __init__(self):
        self.base_prt = 0
        self.name = ''
        self.fps = 0.0
        self.flags = AnimDescFlags(0)
        self.frame_count = 0
        self.anim_block_id = 0
        self.anim_offset = 0
        self.anim_block_ikrule_offset = 0
        self.zeroframe_span = 0
        self.zeroframe_count = 0
        self.zeroframe_offset = 0
        self.zeroframe_stall_time = 0
        self.anim_block = 0

        self.animation_frames = []

    def read(self, reader: ByteIO):
        entry = reader.tell()
        self.base_prt = reader.read_int32()
        self.name = reader.read_source1_string(entry)
        self.fps = reader.read_float()
        self.flags = AnimDescFlags(reader.read_int32())
        self.frame_count = reader.read_int32()

        movement_count = reader.read_int32()
        movement_offset = reader.read_int32()

        ikrule_zeroframe_offset = reader.read_int32()

        reader.skip(4 * 5)

        self.anim_block_id = reader.read_int32()
        self.anim_offset = reader.read_int32()

        ikrule_count = reader.read_int32()
        ikrule_offset = reader.read_int32()
        self.anim_block_ikrule_offset = reader.read_int32()

        local_hierarchy_count = reader.read_int32()
        local_hierarchy_offset = reader.read_int32()

        section_offset = reader.read_int32()
        section_frame_count = reader.read_int32()

        self.zeroframe_span = reader.read_int16()
        self.zeroframe_count = reader.read_int16()
        self.zeroframe_offset = reader.read_int32()

        self.zeroframe_stall_time = reader.read_float()

        if section_offset != 0 and section_frame_count > 0:
            self.read_frames()
        else:
            section_id = 0
            self.read_frames(entry + self.anim_offset, section_id)

    def read_frames(self, offset, section_id):
        if self.flags & AnimDescFlags.FRAMEANIM:
            raise NotImplementedError()
        else:
            pass

