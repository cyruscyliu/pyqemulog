from unittest import TestCase
from pyqemulog import get_pql
from pyqemulog import ARM, MIPS, LITTLE, BIG, ARMEL, MIPSEL, MIPSEB


ARMEL_TRACE = 'tests/armel.trace'
MIPSEL_TRACE = 'tests/mipsel.trace'
MIPSEB_TRACE = 'tests/mipseb.trace'


class TestCommon(TestCase):
    def test_get_pql(self):
        pql = get_pql(ARM, LITTLE, ARMEL_TRACE)
        self.assertIsNotNone(pql)
        pql = get_pql(ARMEL, ARMEL_TRACE)
        self.assertIsNotNone(pql)

        pql = get_pql(MIPS, LITTLE, MIPSEL_TRACE)
        self.assertIsNotNone(pql)
        pql = get_pql(MIPSEL, MIPSEL_TRACE)
        self.assertIsNotNone(pql)

        pql = get_pql(MIPS, BIG, MIPSEB_TRACE)
        self.assertIsNotNone(pql)
        pql = get_pql(MIPSEB, MIPSEB_TRACE)
        self.assertIsNotNone(pql)

    def test_generator_mode(self):
        pql = get_pql(ARMEL, ARMEL_TRACE, mode='generator')
        pql.load_in_asm()
        self.assertIsNotNone(pql.bbs)
        self.assertNotEqual(len(pql.bbs), 0)
        self.assertIsNone(pql.cpurfs)
        for k, cpurf in pql.get_cpurf():
            self.assertIsNotNone(cpurf)
            bb = pql.get_bb(cpurf)
            self.assertIsNotNone(bb)
        self.assertIsNotNone(pql.cpurfs)

        pql = get_pql(MIPSEL, MIPSEL_TRACE, mode='generator')
        pql.load_in_asm()
        self.assertIsNotNone(pql.bbs)
        self.assertNotEqual(len(pql.bbs), 0)
        self.assertIsNone(pql.cpurfs)
        for k, cpurf in pql.get_cpurf():
            self.assertIsNotNone(cpurf)
            bb = pql.get_bb(cpurf)
            self.assertIsNotNone(bb)
        self.assertIsNotNone(pql.cpurfs)

        pql = get_pql(MIPSEB, MIPSEB_TRACE, mode='generator')
        pql.load_in_asm()
        self.assertIsNotNone(pql.bbs)
        self.assertNotEqual(len(pql.bbs), 0)
        self.assertIsNone(pql.cpurfs)
        for k, cpurf in pql.get_cpurf():
            self.assertIsNotNone(cpurf)
            bb = pql.get_bb(cpurf)
            self.assertIsNotNone(bb)
        self.assertIsNotNone(pql.cpurfs)

    def test_plain_mode(self):
        pql = get_pql(ARMEL, ARMEL_TRACE)
        pql.load_cpurf()
        pql.load_in_asm()
        self.assertIsNotNone(pql.bbs)
        self.assertNotEqual(len(pql.bbs), 0)
        for k, cpurf in pql.get_cpurf():
            self.assertIsNotNone(cpurf)
            bb = pql.get_bb(cpurf)
            self.assertIsNotNone(bb)

        pql = get_pql(MIPSEL, MIPSEL_TRACE)
        pql.load_cpurf()
        pql.load_in_asm()
        self.assertIsNotNone(pql.bbs)
        self.assertNotEqual(len(pql.bbs), 0)
        for k, cpurf in pql.get_cpurf():
            self.assertIsNotNone(cpurf)
            bb = pql.get_bb(cpurf)
            self.assertIsNotNone(bb)

        pql = get_pql(MIPSEB, MIPSEB_TRACE)
        pql.load_cpurf()
        pql.load_in_asm()
        self.assertIsNotNone(pql.bbs)
        self.assertNotEqual(len(pql.bbs), 0)
        for k, cpurf in pql.get_cpurf():
            self.assertIsNotNone(cpurf)
            bb = pql.get_bb(cpurf)
            self.assertIsNotNone(bb)

    def test_readme(self):
        pql = get_pql(ARM, LITTLE, ARMEL_TRACE)
        pql.load_cpurf()
        pql.load_in_asm()

        for cpurf in pql.cpurfs.values():
            bb = pql.get_bb(cpurf)
            self.assertIsNotNone(cpurf)
            self.assertIsNotNone(bb)
