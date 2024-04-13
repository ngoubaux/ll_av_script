#!/usr/bin/env python3

import subprocess
import sys

if __name__ == '__main__':
    subprocess.run(['pipenv', 'run', './ll_sd2towav-env.py'] + sys.argv[1:] )