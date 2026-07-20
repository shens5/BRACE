# BRACE
Biomedical Robotics Architecture for Clinical Experimentation (BRACE): A Software Framework for Clinical Robotics Research

Install with:
```
pip install brace-robotics
pip install brace-robotics[can] # for installing CAN dependencies (if used)
pip install brace-robotics[zaber] # for installing zaber dependences (if used in other example)
```

## Examples:

### Exoskeleton Example
Run the code on embedded computer (such as Raspberry Pi) based on our Exoskeleton set up:
```
python -m brace.example.exoskeleton.ServerSide
```

From the client side (such as a laptop), run with:
```
python -m brace.example.exoskeleton.mainGUI
```

### Zaber Example
Run the code on embedded computer (such as Raspberry Pi) based on our Zaber set up:
```
python -m brace.example.zaber.ZaberServerSide
```

From the client side (such as a laptop), run with:
```
python -m brace.example.zaber.zaberMain
```

----
Attributions:
"Diskette Save SVG Vector" by SVG Repo is licensed under CC0 1.0 Universal PD Dedication. https://www.svgrepo.com/svg/193811/diskette-save
