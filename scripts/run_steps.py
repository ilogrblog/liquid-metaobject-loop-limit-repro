#!/usr/bin/env python3
"""Seed 49, 50, 51, 249, 250 and 251 entries in turn and read the probe after each step.

Usage: STORE_PASSWORD=... [PROBE_PATH=/cart] [APP_PATH=<app folder>] run_steps.py <store>.myshopify.com <theme-id> <type> <out-file>
After each seeding step it polls the storefront until values_count equals the seeded
number (or 90 s pass), then appends the probe lines to <out-file>. At 250 and 251 it
also records the ?page=N and keyed page-parameter requests.
"""
import os, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__))
store, theme, mtype, out = sys.argv[1:5]

def read(pages=False):
    cmd = [sys.executable, os.path.join(here, "read_probe.py"), store, theme] + (["--pages"] if pages else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.stdout + p.stderr

with open(out, "a") as f:
    for n in (49, 50, 51, 249, 250, 251):
        subprocess.run([sys.executable, os.path.join(here, "seed.py"), store, mtype, str(n)], check=True)
        t0 = time.time()
        while True:
            txt = read()
            if "values_count=%d " % n in txt or time.time() - t0 > 90:
                break
            time.sleep(5)
        waited = round(time.time() - t0)
        if "values_count=%d " % n in txt and n in (250, 251):
            txt = read(pages=True)
        block = "== seeded %d (waited %d s for the reported count) ==\n%s\n" % (n, waited, txt)
        print(block, flush=True)
        f.write(block)
