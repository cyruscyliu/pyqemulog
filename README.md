# pyqemulog

This is the [qemu-log](https://github.com/organix/qemu-log) ported to Python.
It converts the structured trace generated by QEMU with -d enabled to JSON.

## Usage

#### QEMU side

```
qemu-system-${ARCH} ... -d cpu,in_asm[,int] -D tracefile
```

#### PYQEMULOG side

```python
from pyqemulog import get_pql

pql = get_pql(ARCH, 'tracefile')
pql.load_cpurf()
pql.load_in_asm()

for cpurf in pql.cpurfs.values():
    bb = pql.get_bb(cpurf)
    print(bb) # cpurf's basic blocks
    print(cpurf) # bb's cpu register files
```

#### ARCH table
|ARCH|arch|endian|
|:-:|:-:|:-:|
|armel|arm|l|
|mipsel|mips|l|
|mipseb|mips|b|

## Contribution

It's welcome to contribute pyqemulog!
