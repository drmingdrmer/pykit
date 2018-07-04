#!/usr/bin/env python2
# coding: utf-8

import unittest

from pykit import cluster
from pykit import ututil
from pykit.cluster import BlockDesc
from pykit.cluster import BlockID

dd = ututil.dd


class TestClusterRegion(unittest.TestCase):

    def test_init(self):

        region_cases = [
            [{},
                {'idc': None, 'range': [None, None], 'levels': []}],
            [{'range': ['a', 'b'], 'idc': '.bei'},
                {'idc': '.bei', 'range': ['a', 'b'], 'levels': []}],
            [{'levels': [[['a', 'b', BlockDesc()]], [['c', 'd', BlockDesc(size=1)]]]},
                {'idc': None, 'range': [None, None], 'levels': [[['a', 'b', BlockDesc()]], [['c', 'd', BlockDesc(size=1)]]]}],
            [{'range': ['a', 'z'], 'levels': [[['a', 'b', BlockDesc()], ['b', 'c', BlockDesc(size=2)]]]},
                {'idc': None, 'range': ['a', 'z'], 'levels': [[['a', 'b', BlockDesc()], ['b', 'c', BlockDesc(size=2)]]]}],
        ]

        for case, excepted in region_cases:

            region = cluster.Region(case)

            case['idc'] = 'beijing'
            case['test'] = {'a': 1}
            if 'levels' in case:
                case['levels'].append(['d', 'e', 5])

            self.assertEqual(excepted, region)

        region_cases_argkv = [
            ([[['a', 'b', BlockDesc(size=1)], ['c', 'd', BlockDesc(size=2)]]],
                {'idc': None, 'range': [None, None], 'levels': [[['a', 'b', BlockDesc(size=1)], ['c', 'd', BlockDesc(size=2)]]]}),
            (['a', 'z'],
                {'idc': None, 'range': ['a', 'z'], 'levels': []}),
            ([],
                {'idc': None, 'range': ['a', 'z'], 'levels': [[['a', 'b', BlockDesc(size=1)], ['c', 'd', BlockDesc(size=2)]], [['f', 'g', BlockDesc(size=5)]]]}),
        ]

        region = cluster.Region(levels=region_cases_argkv[0][0])
        region_cases_argkv[0][0].append([['f', 'g', BlockDesc(size=5)]])
        self.assertEqual(region_cases_argkv[0][1], region)

        region = cluster.Region(range=region_cases_argkv[1][0])
        self.assertEqual(region_cases_argkv[1][1], region)

        region = cluster.Region(
            levels=region_cases_argkv[0][0], range=region_cases_argkv[1][0])
        self.assertEqual(region_cases_argkv[2][1], region)

    def test_move_down(self):

        region_levels = [
            [['aa', 'ee', BlockDesc(size=1)], ['hh', 'hz', BlockDesc(size=2)], [
                'pp', 'zz', BlockDesc(size=3)], ['zz', None, BlockDesc(size=4)]],
            [['cf', 'cz', BlockDesc(size=5)], ['mm', 'oo', BlockDesc(size=6)], ['oo', 'qq', BlockDesc(size=7)]],
            [['aa', 'bb', BlockDesc(size=8)], ['cc', 'cd', BlockDesc(size=9)], ['ee', 'ff', BlockDesc(size=10)]],
            [['aa', 'ab', BlockDesc(size=11)], ['az', 'bb', BlockDesc(size=12)], ['za', None, BlockDesc(size=13)]],
            [['d', 'fz', BlockDesc(size=14)]],
        ]

        excepted_region_levels = [
            [['aa', 'ee', BlockDesc(size=1)], ['ee', 'ff', BlockDesc(size=10)], ['hh', 'hz', BlockDesc(size=2)], [
                'mm', 'oo', BlockDesc(size=6)], ['pp', 'zz', BlockDesc(size=3)], ['zz', None, BlockDesc(size=4)]],
            [['aa', 'bb', BlockDesc(size=8)], ['cc', 'cd', BlockDesc(size=9)], ['cf', 'cz', BlockDesc(size=5)], [
                'd', 'fz', BlockDesc(size=14)], ['oo', 'qq', BlockDesc(size=7)], ['za', None, BlockDesc(size=13)]],
            [['aa', 'ab', BlockDesc(size=11)], ['az', 'bb', BlockDesc(size=12)]],
        ]

        excepted_moved_blocks = [
            (1, 0, ['mm', 'oo', BlockDesc(size=6)]),
            (2, 1, ['aa', 'bb', BlockDesc(size=8)]),
            (2, 1, ['cc', 'cd', BlockDesc(size=9)]),
            (2, 0, ['ee', 'ff', BlockDesc(size=10)]),
            (3, 2, ['aa', 'ab', BlockDesc(size=11)]),
            (3, 2, ['az', 'bb', BlockDesc(size=12)]),
            (3, 1, ['za', None, BlockDesc(size=13)]),
            (4, 1, ['d', 'fz', BlockDesc(size=14)]),
        ]

        region = cluster.Region(levels=region_levels)
        moved_blocks = region.move_down()

        self.assertEqual(excepted_moved_blocks, moved_blocks)
        self.assertEqual(excepted_region_levels, region['levels'])

        region_levels = [
            [['aa', 'ee', BlockDesc(size=1)], ['ee', 'ff', BlockDesc(size=10)], ['hh', 'hz', BlockDesc(size=2)]],
            [['aa', 'yy', BlockDesc(size=8)]]
        ]

        region = cluster.Region(levels=region_levels)
        moved_blocks = region.move_down()

        self.assertEqual([], moved_blocks)
        self.assertEqual(region_levels, region['levels'])

    def test_find_merge(self):

        region_levels_cases = [
            [
                [
                    [['aa', 'ee', {'size': 8}], ['ee', 'ff', {'size': 16}], [
                        'pp', 'zz', {'size': 8}], ['zz', None, {'size': 4}]],
                    [['aa', 'pz', {'size': 4}], ['qq', 'zz', {'size': 8}]]
                ],
                (1, ['qq', 'zz', BlockDesc(size=8)], [['pp', 'zz', BlockDesc(size=8)]])
            ],
            [
                [
                    [['aa', 'ee', {'size': 8}], ['ee', 'ff', {
                        'size': 8}], ['hh', 'hz', {'size': 8}]],
                    [['mm', 'yy', {'size': 8}]]
                ],
                None
            ]
        ]

        for levels, excepted in region_levels_cases:
            region = cluster.Region(levels=levels)
            res = region.find_merge()

            self.assertEqual(excepted, res)

    def test_list_block_ids(self):

        bid1 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000001')
        bid2 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000002')
        bid3 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000003')
        bid4 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000004')
        bid5 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000005')
        bid6 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000006')

        region_levels = [
            [['aa', 'ee', {'block_id': bid1}],
                ['hh', 'zz', {'block_id': bid2}]],
            [['ea', 'ff', {'block_id': bid4}],
                ['mm', 'yy', {'block_id': bid5}]],
        ]

        cases = (
                (None, [bid1, bid2, bid4, bid5]),
                (bid3, [bid4, bid5]),
                (bid5, [bid5]),
                (bid6, []),
        )

        region = cluster.Region(levels=region_levels)

        for bid, excepted in cases:
            block_ids = region.list_block_ids(start_block_id=bid)
            self.assertEqual(excepted, block_ids)

    def test_replace_block_id(self):

        bid1 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000001')
        bid2 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000002')
        bid3 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000003')
        bid4 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000004')
        bid5 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000005')
        bid6 = BlockID.parse('d1g0006300000001230101c62d8736c72800020000000006')

        region_levels = [
            [['aa', 'ee', {'block_id': bid1}], ['hh', 'zz', {'block_id': bid2}]],
            [['ea', 'ff', {'block_id': bid4}], ['mm', 'yy', {'block_id': bid5}]],
        ]

        excepted_region_levels = [
            [['aa', 'ee', BlockDesc({'block_id': bid1})], ['hh', 'zz', BlockDesc({'block_id': bid2})]],
            [['ea', 'ff', BlockDesc({'block_id': bid3})], ['mm', 'yy', BlockDesc({'block_id': bid5})]],
        ]

        region = cluster.Region(levels=region_levels)

        region.replace_block_id(bid4, bid3)
        self.assertEqual(excepted_region_levels, region['levels'])

        self.assertRaises(cluster.BlockNotInRegion,
                          region.replace_block_id, bid6, bid1)

    def test_add_block(self):

        region_cases = (
            (
                {},
                (['a', 'c'], BlockDesc(), None),
                {'idc': None, 'range': [None, None], 'levels': [
                    [['a', 'c', BlockDesc()]],
                ]},
                None,
            ),
            (
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)], ['b', 'c', BlockDesc(size=2)]],
                ]},
                (['c', 'd'], BlockDesc(), None),
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)], ['b', 'c', BlockDesc(size=2)]],
                    [['c', 'd', BlockDesc()]],
                ]},
                None,
            ),
            (
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)]],
                    [['b', 'c', BlockDesc(size=2)]],
                ]},
                (['c', 'd'], BlockDesc(), 0),
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)], ['c', 'd', BlockDesc()]],
                    [['b', 'c', BlockDesc(size=2)]],
                ]},
                None,
            ),
            (
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)]],
                    [['b', 'c', BlockDesc(size=2)]],
                ]},
                (['c', 'd'], BlockDesc(), 1),
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)]],
                    [['b', 'c', BlockDesc(size=2)], ['c', 'd', BlockDesc()]],
                ]},
                None,
            ),
            (
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)]],
                    [['b', 'c', BlockDesc(size=2)]],
                ]},
                (['c', 'd'], BlockDesc(), 2),
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)]],
                    [['b', 'c', BlockDesc(size=2)]],
                    [['c', 'd', BlockDesc()]],
                ]},
                None,
            ),
            (
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)]],
                    [['b', 'c', BlockDesc(size=2)]],
                ]},
                (['c', 'd'], BlockDesc(), 3),
                {'idc': 'test', 'range': ['a', 'z'], 'levels': [
                    [['a', 'b', BlockDesc(size=1)]],
                    [['b', 'c', BlockDesc(size=2)]],
                ]},
                cluster.LevelOutOfBound,
            ),
        )

        for case, args, excepted, err in region_cases:
            region = cluster.Region(case)

            if err is not None:
                self.assertRaises(err, region.add_block, *args)
                continue

            region.add_block(*args)

            self.assertEqual(excepted, region)
