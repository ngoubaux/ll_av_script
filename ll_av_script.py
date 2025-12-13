#!/usr/bin/env python3
"""
ll_av_script - Audio/Video Processing Script
Main entry point for the refactored application
"""

import subprocess
import sys

if __name__ == '__main__':
    subprocess.run(['pipenv', 'run', './ll_av_script-env.py'] + sys.argv[1:])
