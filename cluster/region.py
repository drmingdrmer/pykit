#!/usr/bin/env python
# coding: utf-8

import bisect
import copy

from pykit import rangeset
from .block_desc import BlockDesc
from .block_id import BlockID


class BlockNotInRegion(Exception):
    pass


class LevelOutOfBound(Exception):
    pass


class Region(dict):

    fields_default = {'idc': None,
                      'range': [None, None],
                      'levels': [], }

    def __init__(self, region=None, **argkv):

        self.update(copy.deepcopy(self.fields_default))

        if region is not None:
            self.update(copy.deepcopy(region))

        self.update(copy.deepcopy(argkv))

        self['range'] = rangeset.Range(*self['range'])

        for level, blocks in enumerate(self['levels']):
            for b in blocks:
                b[2] = BlockDesc(b[2])

            self['levels'][level] = rangeset.RangeDict(blocks)

    def need_merge(self, source, targets):

        src_blk_size = source[2]['size']

        target_blk_size = 0
        for target in targets:
            target_blk_size += target[2]['size']

        return 4 * src_blk_size >= target_blk_size

    def find_moved_to_level(self, src_block, src_level, region_levels):

        for level in reversed(range(src_level)):

            blocks = region_levels[level]
            overlapped = blocks.find_overlapped(src_block)

            if len(overlapped) != 0:
                level += 1
                return level

        return 0

    def move_down(self):

        region_levels = self['levels']
        moved_blocks = []

        for level, src_blocks in enumerate(region_levels):
            if level == 0:
                continue

            for src in src_blocks[:]:
                target_level = self.find_moved_to_level(
                    src, level, region_levels)
                if level == target_level:
                    continue

                moved_blocks.append((level, target_level, src))

                region_levels[level].remove(src)
                region_levels[target_level].add(src[:2], src[2])

        while region_levels[-1] == []:
            region_levels.pop(-1)

        return moved_blocks

    def find_merge(self):

        region_levels = self['levels']

        for level, src_blocks in enumerate(region_levels):
            if level == 0:
                continue

            lower_blocks = region_levels[level - 1]

            for src in src_blocks:
                overlapped = lower_blocks.find_overlapped(src)

                if len(overlapped) == 0:
                    continue

                if self.need_merge(src, overlapped):
                    return (level, src, overlapped)

    def list_block_ids(self, start_block_id=None):

        block_ids = []

        for blocks in self['levels']:
            level_bids = [b[2]['block_id'] for b in blocks]
            block_ids.extend(level_bids)

        block_ids.sort()

        if start_block_id is not None:
            start_block_id = BlockID.parse(start_block_id)
            idx = bisect.bisect_left(block_ids, start_block_id)
            block_ids = block_ids[idx:]

        return block_ids

    def replace_block_id(self, block_id, new_block_id):
        block_id = BlockID.parse(block_id)
        new_block_id = BlockID.parse(new_block_id)

        for blocks in self['levels']:

            for block in blocks:
                if block[2]['block_id'] == block_id:
                    block[2]['block_id'] = new_block_id
                    return

        raise BlockNotInRegion('block_id: %s' % str(block_id))

    def add_block(self, active_range, block, level=None):

        max_level = len(self['levels']) - 1

        if level is None:
            level = max_level + 1

        elif level < 0 or level > max_level + 1:
            raise LevelOutOfBound('level is invalid. except level >= 0 and level <= {0}, '
                                  'got: {1}'.format(max_level+1, level))

        if level == max_level+1:
            self['levels'].append(rangeset.RangeDict())

        desc = BlockDesc(block)
        self['levels'][level].add(active_range, desc)
