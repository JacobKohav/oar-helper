import argparse
import subprocess
import os
import json
import subprocess
import re

from datetime import datetime
from collections import defaultdict

# Helper functions for executing commandline commands
def run_basic(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

def run_advanced(command):
    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

# Helper function to parse `lscpu`
def parse_lscpu(output):
    parsed = {}
    current_category = "general"
    parsed[current_category] = {}

    for line in output.splitlines():
        if not line.strip():
            continue
        if ':' not in line:
            continue  # Skip malformed lines

        key, value = map(str.strip, line.split(":", 1))

        # Categorize based on keyword in key
        key_lower = key.lower()
        if key_lower.startswith("vulnerability"):
            parsed.setdefault("vulnerabilities", {})[key.replace("Vulnerability ", "")] = value
        elif key_lower.startswith("l1") or key_lower.startswith("l2") or key_lower.startswith("l3"):
            parsed.setdefault("cache", {})[key] = value
        elif key_lower.startswith("numa"):
            parsed.setdefault("numa", {})[key] = value
        else:
            parsed[current_category][key] = value

    return parsed

# ///////////////////////////////////////////////////////////////////////
# Helper functions for Node File info
def format_properties_line(line):
    entries = [kv.strip() for kv in line.split(',') if kv.strip()]
    kv_pairs = []
    for entry in entries:
        if '=' in entry:
            k, v = entry.split('=', 1)
            kv_pairs.append((k.strip(), v.strip().strip("'\"")))
    max_key_len = max(len(k) for k, _ in kv_pairs)
    return "\n".join(f"{k.ljust(max_key_len)} = {v}" for k, v in kv_pairs)

def format_full_properties(raw_text):
    blocks = raw_text.strip().split('\n')
    return "\n\n".join(format_properties_line(block) for block in blocks)
# ////////////////////////////////////////////////////////////////////////

def get_gpu_info_unformatted():
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return (result.stdout)
    except subprocess.CalledProcessError as e:        # with open(output_path, "w") as f:
            # f.write(result.stdout)
        print("Failed to run nvidia-smi:", e.stderr)

def get_gpu_info_json():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        lines = result.stdout.strip().splitlines()
        gpus = []
        for line in lines:
            name, memory, driver = [part.strip() for part in line.split(",")]
            gpus.append({
                "name": name,
                "memory_total_MB": int(memory),
                "driver_version": driver
            })

        # format as true json
        gpus = {
            f"gpu_{i}": gpu for i, gpu in enumerate(gpus)
        }

        return gpus
    except subprocess.CalledProcessError as e:
        print("Failed to query GPU info:", e.stderr)
        return []

def get_machine_info_json():
    info = {
        "job_id": os.getenv("OAR_JOB_ID"),
        "host_hostname": os.getenv("HOST_HOSTNAME"),
        "hostname": run_basic(["hostname"]),
        "cpu_info": parse_lscpu(run_basic(["lscpu"])),
        "gpu_info": get_gpu_info_json(),
        # "nodes": open(os.getenv("OAR_NODE_FILE")).read().strip().splitlines()
    }

    return (info)
    # print (formatted)

def get_machine_info_unformatted():
    result = f"OAR_JOB_ID:               {os.getenv('OAR_JOB_ID')}"
    result = "%s\n%s" % (result, f"HOST_HOST_NAME:           {os.environ.get('HOST_HOSTNAME')}")
    result = "%s\n%s" % (result, f"hostname:                 {run_basic(['hostname'])}")

    try:
        lscpu_result = subprocess.run(
            ["script", "-q", "-c", "lscpu", "/dev/null"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        result = "%s\n\nCPU Info:\n%s" % (result, lscpu_result.stdout)
    except subprocess.CalledProcessError as e:        # with open(output_path, "w") as f:
            # f.write(result.stdout)
        print("Failed to run lscpu:", e.stderr)
    
    result = "%s\n\nGPU Info:\n%s" % (result, f"{get_gpu_info_unformatted()}")

    # //////////////////////////////
    # Testing just oar_resource_prop
    # file_path = "/etc/oar_resource_props"

    # with open("/etc/oar_resource_props", "r") as f:
    #     raw_data = f.read()

    # formatted = format_full_properties(raw_data)
    # return (formatted)
    # //////////////////////////////

    return (result)

if '__main__' in __name__:
    now = datetime.utcnow()
    timestamp = f"{now.year}-({now.strftime('%m')}){now.strftime('%b').upper()}-{now.strftime('%d')}_{now.strftime('%H')}h{now.strftime('%M')}m{now.strftime('%S')}s--UTC"

    parser = argparse.ArgumentParser(description=' ')
    parser.add_argument('-t', '--timestamp', type=str)
    parser.add_argument('-d', '--basepath', type=str, help="Index of key", default=0)

    args = parser.parse_args()

    # local_base_path = ""
    machine_base_path = "/home/jkohav/jack/diverse_assets"
    base_path="/diverse-experiments/starcoder_experim/scripts/results/hw_info"

    gpu_unformatted = get_gpu_info_unformatted()
    with open(f"{machine_base_path}{base_path}/gpu_info_{timestamp}.txt", "w") as f:
        f.write(gpu_unformatted)
    print(f"\nGPU info saved as `.txt` to\n {machine_base_path}{base_path}/gpu_info_{timestamp}.txt")

    gpu_json=get_gpu_info_json()
    with open(f"{machine_base_path}{base_path}/gpu_info_{timestamp}.json", "w") as f:
        json.dump(gpu_json, f, indent=2)
    print(f"\nGPU info saved as `.json` to\n   {machine_base_path}{base_path}/gpu_info_{timestamp}.json")

    machine_json=get_machine_info_json()
    # print (machine_json)
    with open(f"{machine_base_path}{base_path}/machine_info_{timestamp}.json", "w") as f:
        json.dump(machine_json, f, indent=2)
    print(f"\nMachine info saved as `.json` to\n   {machine_base_path}{base_path}/machine_info_{timestamp}.json")

    machine_unformatted = get_machine_info_unformatted()
    # print (machine_unformatted)
    with open(f"{machine_base_path}{base_path}/machine_info_{timestamp}.txt", "w") as f:
        f.write(machine_unformatted)
    print(f"\nMachine info saved as `.txt` to\n   {machine_base_path}{base_path}/machine_info_{timestamp}.txt")

    print ()