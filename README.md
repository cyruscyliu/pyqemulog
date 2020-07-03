# pyqemulog

This is the [qemu-log](https://github.com/organix/qemu-log) ported to Python.


## Usage

#### QEMU side

```
qemu-system-${ARCH} ... -d cpu,in_asm[,int] -D tracefile
```

#### PYQEMULOG side

```python
from pyqemulog import get_pql

path_to_qemulog = 'tracefile'
pql = get_pql(ARCH, path_to_qemulog)
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
|arm|arm|l|
|mipsel|mips|l|
|mipseb|mips|b|
