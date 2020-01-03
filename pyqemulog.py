import abc
import json

PQL_ARCH_AARCH32 = 0
PQL_ARCH_AARCH64 = 1
PQL_ARCH_MIPS32 = 2
PQL_ARCH_MIPS64 = 3

PQL_BIG_ENDIAN = 0
PQL_LITTLE_ENDIAN = 1


class PQLI(object):
    def __init__(self, endian, path_to_qemulog):
        self.endian = endian
        self.cpurfs = None
        self.bbs = None
        self.path_to_qemulog = path_to_qemulog

    @abc.abstractmethod
    def load_cpurf(self, dump=True):
        pass

    def load_in_asm(self, dump=True):
        """
        ----------------                                1
        IN:                                             2
        0x00000000:  e3a00000  mov      r0, #0          3
        0x00000004:  e59f1004  ldr      r1, [pc, #4]    4
        0x00000008:  e59f2004  ldr      r2, [pc, #4]    4
        0x0000000c:  e59ff004  ldr      pc, [pc, #4]    4
                                                        4 (end)
        """
        ln = 0  # ln number
        bbs = {}  # to be returned

        def parse_in_asm(line):
            things = line.strip().split()
            address = things[0][2:-1]  # remove 0x and :
            raw = things[1]
            opcode = things[2]
            operand = things[3:]
            offset = ln + 1
            return offset, address, raw, opcode, operand

        with open(self.path_to_qemulog) as f:
            state = 0
            for line in f:
                if state == 0 and line.startswith('---'):
                    state = 1
                if state == 3:
                    offset, address, raw, opcode, operand = parse_in_asm(line)
                    bb_id = address
                    new_bb = {'in': address, 'chained': False, 'instructions': [
                        {'ln': offset, 'address': address, 'raw': raw, 'opcode': opcode, 'operand': operand}]}
                    if bb_id in bbs:
                        chained_bb = bbs[bb_id]
                        while chained_bb['chained'] and 'next' in chained_bb:
                            chained_bb = chained_bb['next']
                        chained_bb['chained'] = True
                        chained_bb['next'] = new_bb
                    else:
                        new_bb['chained'] = False
                        bbs[bb_id] = new_bb
                if state == 4 and len(line.strip()):
                    offset, address, raw, opcode, operand = parse_in_asm(line)
                    new_bb['instructions'].append(
                        {'ln': offset, 'address': address, 'raw': raw, 'opcode': opcode, 'operand': operand})
                if state in [1, 2, 3]:
                    state += 1
                if state == 4 and not len(line.strip()):
                    new_bb['size'] = len(new_bb['instructions'])
                    state = 0
                ln += 1

        self.bbs = bbs
        if not dump:
            return

        # dump
        with open('in_asm.json', 'w') as f:
            json.dump(bbs, f)

    @abc.abstractmethod
    def get_pc(self, cpurf):
        pass

    def get_bb(self, cpurf):
        bb_id = self.get_pc(cpurf)

        target_bb = self.bbs[bb_id]
        max_ln = cpurf['ln']
        while target_bb['instructions'][-1]['ln'] < max_ln:
            if not target_bb['chained']:
                break
            next_bb = target_bb['next']
            if next_bb['instructions'][-1]['ln'] > max_ln:
                break
            else:
                target_bb = next_bb
        return target_bb

    def get_next_cpurf(self, cpurf):
        try:
            return self.cpurfs[cpurf['id'] + 1]
        except KeyError:
            return None

    def get_next_bb(self, cpurf):
        return self.get_bb(self.get_next_cpurf(cpurf))

    def get_last_cpurf(self, cpurf):
        try:
            return self.cpurfs[cpurf['id'] - 1]
        except KeyError:
            return None

    def get_last_bb(self, cpurf):
        return self.get_bb(self.get_last_cpurf(cpurf))

    def get_exception_return_cpurf(self, cpurf):
        while cpurf:
            if 'exception' in cpurf and \
                    'ret' in cpurf['exception'] and cpurf['exception']['ret']:
                break
            cpurf = self.get_next_cpurf(cpurf)
        return cpurf

    def get_exception_return_bb(self, cpurf):
        return self.get_bb(self.get_exception_return_cpurf(cpurf))


class PQL_AARCH32(PQLI):
    def __init__(self, endian, path_to_qemulog):
        super().__init__(endian, path_to_qemulog)
        self.exception_names = ['unknown', 'unknown', 'svc', 'pabt', 'dabt', 'irq']

    def get_pc(self, cpurf):
        return cpurf['register_files']['R15']

    def load_cpurf(self, dump=True):
        """
        R00=00000055 R01=000e11b0 R02=000f21c4 R03=00000661    1 <- 0
        R04=00000055 R05=00000001 R06=0000b9b0 R07=000e1170    2
        R08=000000a0 R09=00000000 R10=000e11b4 R11=000e2178    3
        R12=000e217c R13=000e215c R14=00008e24 R15=00008d80    4
        PSR=200001d3 --C- A svc32                              5
        AArch32 mode switch from irq to abt PC 0xc000af4c      6 -> 2 or 0 or 6
        Exception return from AArch32 abt to svc PC 0xc0020a00 6 -> 2 or 0 or 6
        Taking exception 4 [Data Abort]                        6 -> 2 or 0 or 6
        ...from EL1 to EL1                                     7
        ...with ESR 0x25/0x9600003f                            8
        ...with DFSR 0x8 DFAR 0xf1012014                       9 -> 0
        Taking exception 5 [IRQ]                               6 -> 2 or 0 or 6
        ...from EL1 to EL1                                     7
        ...with ESR 0x0/0x0                                    8 -> 0
        Taking exception 3 [Prefetch Abort]                    6 -> 2 or 0 or 6
        ...from EL0 to EL1                                     7
        ...with ESR 0x20/0x8200003f                            8
        ...with IFSR 0x17 IFAR 0x400009b0                      9
        """
        ln = 0
        cpurfs = {}

        def parse_state(line):
            psr, flags, _, mode = line.strip().split()
            psr_name, _, psr_value = psr.partition('=')
            return psr_name, psr_value, flags, None, mode

        def parse_rfs(line):
            things = line.strip().split()
            rfs = {}
            for rf in things:
                rf_name, _, rf_value = rf.partition('=')
                rfs[rf_name] = rf_value
            offset = ln + 1
            return offset, rfs

        cpurf_id = 0
        with open(self.path_to_qemulog) as f:
            state = 0
            for line in f:
                if state == 0 and line.startswith('R00'):
                    state = 1
                    offset, rfs = parse_rfs(line)
                    cpurfs[cpurf_id] = {'id': cpurf_id, 'ln': offset, 'register_files': rfs}
                if state in [2, 3, 4]:
                    _, rfs = parse_rfs(line)
                    for rf_name, rf_value in rfs.items():
                        cpurfs[cpurf_id]['register_files'][rf_name] = rf_value
                if state == 5:
                    psr_name, psr_value, flags, _, mode = parse_state(line)
                    cpurfs[cpurf_id]['register_files'][psr_name] = psr_value
                    cpurfs[cpurf_id]['mode'] = mode
                if state == 9:
                    dfr_name_value = line.strip().split()[1:]
                    for i in range(0, len(dfr_name_value), 2):
                        cpurfs[cpurf_id]['register_files'][dfr_name_value[i]] = dfr_name_value[i + 1]
                if state == 6:
                    if line.startswith('R00'):
                        cpurf_id += 1
                        state = 1
                        offset, rfs = parse_rfs(line)
                        cpurfs[cpurf_id] = {'id': cpurf_id, 'ln': offset, 'register_files': rfs}
                    elif line.startswith('Taking exception'):
                        exception_type = int(line.strip().split()[2])
                        exception_name = self.exception_names[exception_type]
                        if 'exception' in cpurfs[cpurf_id]:
                            cpurfs[cpurf_id]['exception']['type'] = exception_name
                        else:
                            cpurfs[cpurf_id]['exception'] = {'type': exception_name}
                    elif line.startswith('Exception return'):
                        _, _, _, _, f, _, t, _, pc = line.strip().split()
                        cpurfs[cpurf_id]['exception'] = {'ret': True, 'from': f, 'to': t, 'pc': pc}
                        state = 5
                    elif line.find('mode switch') != -1:
                        _, _, _, _, f, _, t, _, pc = line.strip().split()
                        cpurfs[cpurf_id]['exception'] = {'switch': True, 'from': f, 'to': t, 'pc': pc}
                        state = 10
                    else:
                        state = 10
                if state == 8:
                    if exception_type in [2, 5]:  # irq
                        state = 10
                if state in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                    state += 1
                if state == 10:
                    state = 0
                    cpurf_id += 1
                ln += 1

        self.cpurfs = cpurfs

        if not dump:
            return

        # dump
        with open('cpu.json', 'w') as f:
            json.dump(cpurfs, f)


class PQL_MIPS32(PQLI):
    def __init__(self, endian, path_to_qemulog):
        super().__init__(endian, path_to_qemulog)

    def load_cpurf(self, dump=True):
        """
        pc=0x80005d0c HI=0x00000000 LO=0x00000000 ds 0090 80005d0c 0        1 <- 0
        GPR00: r0 00000000 at 1000001f v0 00000000 v1 00000000              2
        GPR04: a0 00000000 a1 00000000 a2 00000000 a3 00000000              3
        GPR08: t0 80005d0c t1 00000000 t2 00000000 t3 00000000              4
        GPR12: t4 00000000 t5 00000000 t6 00000000 t7 00000000              5
        GPR16: s0 00000000 s1 00000000 s2 00000000 s3 00000000              6
        GPR20: s4 00000000 s5 00000000 s6 00000000 s7 00000000              7
        GPR24: t8 00000000 t9 00000000 k0 00000000 k1 00000000              8
        GPR28: gp 00000000 sp 00000000 s8 00000000 ra 00000000              9
        CP0 Status  0x10400000 Cause   0x00000000 EPC    0x00000000         10
            Config0 0x80000482 Config1 0x9e190c8f LLAddr 0x0000000000000000 11
            Config2 0x80000000 Config3 0x00000c20                           12
            Config4 0x00000000 Config5 0x00000000                           13
        """
        ln = 0
        cpurfs = {}

        def parse_state(line):
            """
            SR: Soft-Reset, 20
            NMI: Non-Maskable-Interrupt, 19
            IM7-0: Interrupt-Mask, 15-8
            KSU: Kernel-Supervise-User, 4-3
            """
            status = int(line.strip().split()[2], 16)
            mode_value = status >> 3 & 0xFF
            if mode_value == 0:
                mode = 'kernel'
            elif mode_value == 1:
                mode = 'supervisor'
            elif mode_value == 2:
                mode = 'user'
            else:
                raise ValueError('bad status register')
            return mode

        def parse_rfs(line, ref=4, off=1):
            things = line.strip().split()
            rfs = {}
            for i in range(0, ref):
                value = things[off + 1 + 2 * i]
                if value.startswith('0x'):
                    value = value[2:]
                rfs[things[off + 2 * i]] = value
            offset = ln + 1
            return offset, rfs

        cpurf_id = 0
        with open(self.path_to_qemulog) as f:
            state = 0
            for line in f:
                if state == 0 and line.startswith('pc='):
                    state = 1
                    offset, rfs = ln + 1, {'pc': line.strip().split()[-2]}
                    cpurfs[cpurf_id] = {'id': cpurf_id, 'ln': offset, 'register_files': rfs}
                if state in [2, 3, 4, 5, 6, 7, 8, 9]:
                    _, rfs = parse_rfs(line, ref=4, off=1)
                    for rf_name, rf_value in rfs.items():
                        cpurfs[cpurf_id]['register_files'][rf_name] = rf_value
                if state in [10]:
                    mode = parse_state(line)
                    _, rfs = parse_rfs(line, ref=3, off=1)
                    for rf_name, rf_value in rfs.items():
                        cpurfs[cpurf_id]['register_files'][rf_name] = rf_value
                    cpurfs[cpurf_id]['mode'] = mode
                if state in [11]:
                    _, rfs = parse_rfs(line, ref=3, off=0)
                    for rf_name, rf_value in rfs.items():
                        cpurfs[cpurf_id]['register_files'][rf_name] = rf_value
                if state in [12, 13]:
                    _, rfs = parse_rfs(line, ref=2, off=0)
                    for rf_name, rf_value in rfs.items():
                        cpurfs[cpurf_id]['register_files'][rf_name] = rf_value
                if state in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
                    state += 1
                if state == 14:
                    state = 0
                    cpurf_id += 1
                ln += 1

        if not dump:
            return

        with open('cpu.json', 'w') as f:
            json.dump(cpurfs, f)

    def get_pc(self, cpurf):
        return cpurf['register_files']['pc']


def get_pql(arch, endian, path_to_qemulog):
    if arch == 'aarch32':
        return PQL_AARCH32(endian, path_to_qemulog)
    else:
        return PQL_MIPS32(endian, path_to_qemulog)
