# ghidra-skink
Skink: a Python script to convert Ghidra functions and structures to C and C++ header files

## Reading a .gzf instead of a SARIF export

With pyghidra, skink can read a program straight from a Ghidra `.gzf` (File > Export Program..., format
"Ghidra Zip File"), so the SARIF export is not needed. This is much faster: for OpenSHC (Stronghold Crusader),
exporting all headers takes about half a minute instead of about ten.

```sh
pip install "skink[ghidra] @ git+https://github.com/gynt/ghidra-skink"
```

Set `GHIDRA_INSTALL_DIR` to your Ghidra installation, then use `Project.from_gzf` where you would use a SARIF file:

```py
from skink.export.project.project import Project

project = Project.from_gzf("program.gzf")       # instead of Project("program.sarif", ...)
project = Project.from_program(currentProgram)  # or from a Program in a pyghidra script
```

On the command line, `skink export` and `skink sarif extract` take `--input-format gzf`.

The records are the ones skink would decode from a SARIF export of the same program, in the same order, so the
exported headers are the same. To check this for your program:

```sh
skink ghidra verify --gzf program.gzf --sarif program.sarif
```
