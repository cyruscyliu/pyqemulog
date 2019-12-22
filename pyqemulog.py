import json


def do_lines(path_to_qemulog):
    with open(path_to_qemulog) as f:
        for line in f:
            print(line, end='')


def load_cpurf(path_to_qemulog, dump=True):
    """
    R00=00000055 R01=000e11b0 R02=000f21c4 R03=00000661 1 <- 0
    R04=00000055 R05=00000001 R06=0000b9b0 R07=000e1170 2
    R08=000000a0 R09=00000000 R10=000e11b4 R11=000e2178 3
    R12=000e217c R13=000e215c R14=00008e24 R15=00008d80 4
    PSR=200001d3 --C- A svc32                           5
    Taking exception 4 [Data Abort]                     6 -> 1 or 0
    ...from EL1 to EL1                                  7
    ...with ESR 0x25/0x9600003f                         8
    ...with DFSR 0x8 DFAR 0xf1012014                    9 -> 0
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
    exception_names = [
        'Reset', 'Undefined Instruction', 'software Interrupt', 'Prefetch  Abort',
        'Data Abort', 'Reserved', 'IRQ', 'FIQ']
    with open(path_to_qemulog) as f:
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
                    exception_name = exception_names[exception_type]
                    cpurfs[cpurf_id]['exception'] = {'type': exception_type, 'name': exception_name}
                else:
                    state = 10
            if state in [1, 2, 3, 4, 5, 7, 8, 9]:
                state += 1
            if state == 10:
                state = 0
                cpurf_id += 1
            ln += 1

    if not dump:
        return cpurfs
    # dump
    with open('cpu.json', 'w') as f:
        json.dump(cpurfs, f)
    return cpurfs


def load_in_asm(path_to_qemulog, dump=True):
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

    with open(path_to_qemulog) as f:
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

    if not dump:
        return bbs
    # dump
    with open('in_asm.json', 'w') as f:
        json.dump(bbs, f)
    return bbs


def do_parse(path_to_qemulog):
    load_in_asm(path_to_qemulog)
    load_cpurf(path_to_qemulog)


def get_bb(cpurf, bbs):
    bb_id = cpurf['register_files']['R15']

    target_bb = bbs[bb_id]
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


def run(args):
    if args.lines:
        do_lines(args.lines)
    elif args.parse:
        do_parse(args.parse)
    else:
        # will never be executed
        raise NotImplementedError('see help')
