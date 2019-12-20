# pyqemu-log

This is the [qemu-log](https://github.com/organix/qemu-log) ported to Python.

QEMU log parsing utility.

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
    bb = bbs[bb_id]
    print(bb) # cpurf's basic blocks
    print(cpurf) # bb's cpu register files
```

### command line

####pyqemulog lines
```shell script
pyqemulog --lines log.txt
... each line of log is displayed ...
```

#### pyqemulog parse
```shell script
pyqemulog --parse log.txt
```

##### in_asm
Target assembly code instructions corresponding to block with entry at [in_asm.json](in_asm.json).
```text
{
  "00000000": {
    "in": "00000000",
    "instructions": [
      {
        "ln": 3,
        "address": "00000000",
        "raw": "e3a00000",
        "opcode": "mov",
        "oprand": [
          "r0,",
          "#0"
        ]
      },
      {
        "ln": 4,
        "address": "00000004",
        "raw": "e59f1004",
        "opcode": "ldr",
        "oprand": [
          "r1,",
          "[pc,",
          "#4]"
        ]
      },
      {
        "ln": 5,
        "address": "00000008",
        "raw": "e59f2004",
        "opcode": "ldr",
        "oprand": [
          "r2,",
          "[pc,",
          "#4]"
        ]
      },
      {
        "ln": 6,
        "address": "0000000c",
        "raw": "e59ff004",
        "opcode": "ldr",
        "oprand": [
          "pc,",
          "[pc,",
          "#4]"
        ]
      }
    ],
    "size": 4
  },
}
```
##### cpu
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

