# -*- coding: utf-8 -*-
'''
Created on Wed Jun 11 15:30:36 2025

@author: Ryan Johnston (Univeristy of Alberta)

Based on code from Erik Carlson (https://github.com/erikvcarlson/VLASS_Scripts)
'''
import os
import sys
import shutil
import subprocess
import signal

def ignore_sighup():
    """ Ignore SIGHUP so process isn't killed when SSH session closes
    """
    signal.signal(signal.SIGHUP, signal.SIG_IGN)

def setup_directories(base_dir):
    """ Create base, products, and working directories 
    """
    products_dir = os.path.join(base_dir, 'products')
    working_dir = os.path.join(base_dir, 'working')
    os.makedirs(products_dir, exist_ok=True)
    os.makedirs(working_dir, exist_ok=True)
    return products_dir, working_dir

def copy_files(files, dest_dir):
    """ Copy each file in `files` into `dest_dir`
    """
    for f in files:
        if os.path.isfile(f):
            shutil.copy2(f, dest_dir)
            print(f"Copied {f} -> {dest_dir}")
        else:
            print(f"Warning: {f} does not exist or is not a file.", file=sys.stderr)

def run_shell_script(script_path, working_dir, log_file='job.log'):
    """ Run the shell script in `working_dir`, detaching so it survives logout
    """
    if not os.path.isfile(script_path):
        print(f"Error: script {script_path} not found.", file=sys.stderr)
        sys.exit(1)
    # Ensure the script is executable
    os.chmod(script_path, 0o755)
    # Open log file to capture output
    log_path = os.path.join(working_dir, log_file)
    with open(log_path, 'ab') as logf:
        # Detach child process into its own session
        process = subprocess.Popen(
            ['bash', script_path],
            cwd=working_dir,
            stdout=logf,
            stderr=logf,
            preexec_fn=os.setsid
        )
    print(f"Started script {script_path} with PID {process.pid}. Logs at {log_path}")

def main():
    """
    """
    if len(sys.argv) < 3:
        print("Usage: run_tasks.py <base_dir> <script.sh> [file1 file2 ...]", file=sys.stderr)
        sys.exit(1)

    ignore_sighup()
    base_dir = sys.argv[1]
    script = sys.argv[2]
    files = sys.argv[3:]

    products_dir, working_dir = setup_directories(base_dir)
    copy_files(files, working_dir)
    run_shell_script(script, working_dir)

if __name__ == '__main__':
    main()
