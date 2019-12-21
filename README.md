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
from pyqemulog  import load_cpurf, load_in_asm

path_to_qemulog = 'log.txt'
cpurfs = load_cpurf(path_to_qemulog, dump=False) # get all cpu register files
bbs = load_in_asm(path_to_qemulog, dump=False) # get all basic blocks

for cpurf in cpurfs.values():
    bb_id = cpurf['register_files']['R15']

    target_bb = bbs[bb_id]
    max_ln = cpurf['ln']
    while(target_bb['instructions'][-1] < max_ln):
        if target_bb['chained']:
            next_bb = target_bb['next']
            if next_bb['instructions'][-1] > max_ln:    

    

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
##### cpu (execution)
Target assembly cpu register files at [cpu.json](cpu.json).
```text
{
  "0": {
    "id": 0,
    "ln": 8,
    "register_files": {
      "R00": "00000000",
      "R01": "00000000",
      "R02": "00000000",
      "R03": "00000000",
      "R04": "00000000",
      "R05": "00000000",
      "R06": "00000000",
      "R07": "00000000",
      "R08": "00000000",
      "R09": "00000000",
      "R10": "00000000",
      "R11": "00000000",
      "R12": "00000000",
      "R13": "00000000",
      "R14": "00000000",
      "R15": "00000000",
      "PSR": "400001d3"
    },
    "mode": "svc32"
  }
}
```

