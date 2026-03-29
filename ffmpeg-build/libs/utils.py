#!/usr/bin/env python3
import subprocess
from typing import List

def run(cmd: List[str]):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
