# pyqemu-log

This is the [qemu-log](https://github.com/organix/qemu-log) ported to Python.

QEMU log parsing utility.

## contribution
It's welcome to contribute pyqemulog. We still need to support other -d flags and other architecuters(MIPS...).

## Installation
```shell script
git clone https://github.com/cyruscyliu/pyqemulog.git 
cd pyqemulog && sudo -H pip3.7 install .
```

## Usage

### apis
```python
from pyqemulog import load_cpurf, load_in_asm, get_bb

path_to_qemulog = 'log.txt'
cpurfs = load_cpurf(path_to_qemulog, dump=False) # get all cpu register files
bbs = load_in_asm(path_to_qemulog, dump=False) # get all basic blocks

for cpurf in cpurfs.values():
    bb = get_bb(cpurf, bbs)
    print(bb) # cpurf's basic blocks
    print(cpurf) # bb's cpu register files
```

### command line

#### pyqemulog lines
```shell script
pyqemulog --lines log.txt
... each line of log is displayed ...
```

#### pyqemulog parse
```shell script
pyqemulog --parse log.txt
```

##### in_asm (basic blocks)
Target assembly code instructions corresponding to block with entry at [in_asm.json](in_asm.json).
```text
{
  "00008000": {
    "in": "00008000",
    "chained": true,
    "instructions": [{ 
        "ln": 15, "address": "00008000", "raw": "e3a01c06", "opcode": "mov",
        "operand": [ "r1,", "#0x600" ]
      }, {
        "ln": 16, "address": "00008004", "raw": "e3811061", "opcode": "orr",
        "operand": ["r1,", "r1,", "#0x61"]
      }, {
        "ln": 17, "address": "00008008", "raw": "e1a00000", "opcode": "mov",
        "operand": ["r0,", "r0"]
      },
      ....
    ],
    "size": 11,
    "next": {
      "in": "00008000",
      "chained": false,
      "instructions": [{
          "ln": 3677, "address": "00008000", "raw": "e321f0d3", "opcode": "msr",
          "operand": ["cpsr_c,", "#0xd3"]
        }],
      "size": 1
    }
  },
}
```
##### cpu[,int] (execution)
Target assembly cpu register files at [cpu.json](cpu.json).
```text
{
  37: {
    "id": 37,
    "ln": 529,
    "register_files": {
      "R00": "00000055",
      "R01": "f1012000",
      "R02": "00000000",
      "R03": "00000661",
      "R04": "00000055",
      "R05": "00000001",
      "R06": "0000b9b0",
      "R07": "000e1170",
      "R08": "000000a0",
      "R09": "00000000",
      "R10": "000e11b4",
      "R11": "000e2158",
      "R12": "000e215c",
      "R13": "00000000",
      "R14": "00008d9c",
      "R15": "00000010",
      "PSR": "200001d7",
      "DFSR": "0x8",
      "DFAR": "0xf1012000"
    },
    "mode": "abt32",
    "exception": {
      "type": 4,
      "name": "Data Abort"
    }
  },
}
```

