#! /usr/bin/python

import json
import argparse


def do_lines(path_to_qemulog):
    with open(path_to_qemulog) as f:
        for line in f:
            print(line, end='')


def load_cpurf(path_to_qemulog, dump=True):
    """
    R00=00000000 R01=00000000 R02=00000000 R03=00000000 1
    R04=00000000 R05=00000000 R06=00000000 R07=00000000 2
    R08=00000000 R09=00000000 R10=00000000 R11=00000000 3
    R12=00000000 R13=00000000 R14=00000000 R15=00000000 4
    PSR=400001d3 -Z-- A svc32                           5 -> 6 (end)
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
            if state in [1, 2, 3, 4, 5]:
                state += 1
            if state == 6:
                state = 0
                cpurf_id += 1
            ln += 1

    if not dump:
        return cpurfs
    # dump
    with open('cpu.json', 'w') as f:
        c = 0
        dump = {}
        for k, v, in cpurfs.items():
            c += 1
            if c > 100:
                break
            dump[k] = v
        json.dump(dump, f)
        # json.dump(cpurfs, f)
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
                bbs[bb_id] = {'in': address, 'instructions': [
                    {'ln': offset, 'address': address, 'raw': raw, 'opcode': opcode, 'oprand': operand}]}
            if state == 4 and len(line.strip()):
                offset, address, raw, opcode, operand = parse_in_asm(line)
                bbs[bb_id]['instructions'].append(
                    {'ln': offset, 'address': address, 'raw': raw, 'opcode': opcode, 'oprand': operand})
            if state in [1, 2, 3]:
                state += 1
            if state == 4 and not len(line.strip()):
                bbs[bb_id]['size'] = len(bbs[bb_id]['instructions'])
                state = 0
            ln += 1

    if not dump:
        return bbs
    # dump
    with open('in_asm.json', 'w') as f:
        c = 0
        dump = {}
        for k, v in bbs.items():
            c += 1
            if c > 100:
                break
            dump[k] = v
        json.dump(dump, f)
        # json.dump(bbs, f)
    return bbs


def do_parse(path_to_qemulog):
    # load_in_asm(path_to_qemulog)
    load_cpurf(path_to_qemulog)


def run(args):
    if args.lines:
        do_lines(args.lines)
    elif args.parse:
        do_parse(args.parse)
    else:
        # will never be executed
        raise NotImplementedError('see help')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--lines', help='display each line of the log')
    group.add_argument('--parse', help='parse each line of the log', )

    args = parser.parse_args()
    run(args)
