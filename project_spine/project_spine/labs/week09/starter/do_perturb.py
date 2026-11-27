content = open(r"perturb.py").read()
old = chr(32)*4 + "if name == chr(34)+jpeg+chr(34):" + chr(10) + chr(32)*8 + "# TODO 4a" + chr(10)
print("script written")