# oar-helper
OAR resource/task manager wrapper

## Table of Contents
- [Overview](#overview)
  - [What is OAR?](#what-is-oar)
  - [Architecture](#architecture)
- [Problem Statement](#problem-statement)
  - [Gaps identified](#gaps-identified)
- [Structure](#structure)
- [Script Summary](#script-summary)
  - [`oar_jobs_summary.sh`](#oar_jobs_summarysh)
  - [`oar_hw_specs.py`](#oar_hw_specspy)
- [Script Details](#script-details)
  - [`oar_jobs_summary.sh`](#oar_jobs_summarysh-1)
    - [Functionalities](#functionalities)
    - [Interface](#interface)
    - [How it works](#how-it-works)
    - [Outputs](#outputs)
      - [Example output](#example-output)
  - [`oar_hw_specs.py`](#oar_hw_specspy-1)
    - [Functionalities](#functionalities-1)
    - [Interface](#interface-1)
    - [How it works](#how-it-works-1)
    - [Outputs](#outputs-1)
      - [Example outputs](#example-outputs)
        - [Machine information](#machine-information)
        - [GPU information](#gpu-information)
- [References](#references)

# Overview
## What is OAR?
> "OAR is a versatile resource and task manager (also called a batch scheduler) for HPC clusters, and other computing infrastructures (like distributed computing experimental testbeds where versatility is a key).
Overview" <sup><a href="#ref-1">1</a></sup>

## Architecture
> "OAR architecture is based on a database (PostgreSQL (preferred) or MySQL), a script language (Perl) and an optional scalable administrative tool (e.g. Taktuk). It is composed of modules which interact mainly via the database and are executed as independent programs. Therefore, formally, there is no API, the system interaction is completely defined by the database schema. This approach eases the development of specific modules. Indeed, each module (such as schedulers) may be developed in any language having a database access library." <sup><a href="#ref-1">1</a></sup> 

# Problem Statement
Current OAR commands lack various functionalities: these library of scripts helps to remediate these gaps by adding onto existing OAR functions. <sup><a href="#ref-2">2</a></sup>

# Gaps identified
- single source of truth (SoT) job command 
- hardware specifications extraction

# Structure
```
├── LICENSE
├── README.md
└── scripts
    ├── oar_jobs_summary.sh
    └── oar_hw_specs.py
```

# Script Summary
The repository currently provides two helper scripts, each targeting a different operational gap in standard OAR usage.

## `oar_jobs_summary.sh`
This script addresses the lack of a concise single source of truth for a user's jobs. Its coverage is centered on day-to-day queue monitoring: it combines job state, queue, submission time, predicted start time, wait duration, requested host, walltime, and GPU request into a single view. The result is a compact summary for understanding what is running, what is waiting, and when queued work is expected to start.

## `oar_hw_specs.py`
This script addresses the gap around hardware specification extraction for allocated machines. Its coverage is centered on CPU and GPU inventory capture for the current execution environment, along with basic host and OAR job identifiers. The output is intended to make node-level hardware characteristics easier to record and compare across runs.

# Script Details
## `oar_jobs_summary.sh`
### Functionalities
- Builds a per-user summary table from OAR jobs.
- Shows job ID, state, queue, submission date, requested host, walltime, GPU count, scheduled start in UTC, and scheduled start in a user-selected UTC offset.
- Computes a human-readable "time until start" field for jobs that have a predicted schedule.
- Sorts jobs by scheduled start time to make the queue easier to scan.
- Highlights running and waiting jobs with terminal colors when supported.

### Interface
```text
Usage:
  oar_jobs_summary.sh [user_name] [utc_offset]

Inputs:
  user_name: string, optional
    Target OAR username. Defaults to the current shell user.
  utc_offset: integer, optional
    UTC offset in hours used to render a localized scheduled-start column.
    Accepted forms include +2, -5, or 0.
```

### How it works
The script starts from `oarstat -u` and filters the jobs belonging to a target user. For each job, it then queries `oarstat -fj <job_id>` to pull the richer per-job metadata that is not available in the base listing. From that detailed output, it extracts the requested host, walltime, GPU request, and scheduled start time.

It accepts either a username, a UTC offset, or both as positional arguments. If no username is provided, it defaults to the current shell user. If a UTC offset is provided, the script converts the scheduled start time from UTC into that offset and adds a second timestamp column for easier local interpretation. It also computes the remaining delay before the predicted start time, then formats everything into a fixed-width table.

### Outputs
  - stdout: formatted job summary table
    - Columns include job id, state, scheduled start, time until start, requested host, user, submission date, queue, walltime, GPU count, and raw UTC scheduled start.
  - exit_behavior: shell-script execution
    - Produces terminal-colored rows when `tput` is available.

#### Example output
``` json
jkohav@frennes:~/jack$ oar-helper/oar_jobs_summary.sh jkohav -6
JOB_ID   ST SCHED_STRT (UTC-6)    TIME      REQUESTED_HOST                USER    SUBMISSION_DATE     QUE  WALLTIME  GPUS   SCHED_STRT (UTC)    
3589022  R  2026-03-15 15:11:46   22m       abacus8-1.rennes.grid5000.fr  jkohav  2026-03-15 21:11:28 p1   12:0:0    2      2026-03-15 21:11:46 
3584964  W  2026-03-15 20:26:03   5h 36m    abacus9-1.rennes.grid5000.fr  jkohav  2026-03-14 03:37:35 p1   12:0:0    3      2026-03-16 02:26:03 
3584966  W  2026-03-16 11:17:31   20h 27m   abacus16-1.rennes.grid5000.fr jkohav  2026-03-14 03:38:07 p1   12:0:0    3      2026-03-16 17:17:31 
3584967  W  2026-03-17 10:55:11   1d 20h    abacus25-1.rennes.grid5000.fr jkohav  2026-03-14 03:38:29 p1   12:0:0    3      2026-03-17 16:55:11 
3588193  W  2026-03-18 03:11:17   2d 12h    abacus14-1.rennes.grid5000.fr jkohav  2026-03-15 14:57:10 p1   12:0:0    3      2026-03-18 09:11:17 
```
Note: in an interactive terminal, running jobs are highlighted in green and non-running jobs shown in this summary are highlighted in yellow when terminal color support is available.

## `oar_hw_specs.py`
### Functionalities
- Captures host-level runtime metadata for the current OAR job context.
- Records CPU information from `lscpu`.
- Records GPU information from `nvidia-smi`.
- Produces both raw text outputs and structured JSON outputs.
- Includes OAR-related context such as `OAR_JOB_ID`, host environment variables, and the local hostname.

### Interface
```text
Usage: 
oar_hw_specs.py [-t timestamp] [-d basepath]

Inputs:
  -t, --timestamp: string, optional
    Declared CLI parameter for a custom timestamp.
    Current implementation parses it but does not use it when naming files.
  -d, --basepath: string, optional
    Declared CLI parameter for an output base path.
    Current implementation parses it but does not use it for file writes.
  environment:
    OAR_JOB_ID: string, optional
    HOST_HOSTNAME: string, optional
  system_commands:
    hostname
    lscpu
    nvidia-smi
```

### How it works
The script collects hardware information directly from system commands available on the allocated node. CPU information is gathered through `lscpu` and reorganized into grouped JSON sections such as general CPU data, cache data, NUMA data, and vulnerability data. GPU information is gathered through `nvidia-smi`, both as a raw command dump and as a structured list of GPU model names, memory totals, and driver version.

It then combines that hardware data with basic execution context from environment variables and `hostname`. At runtime, it writes four timestamped artifacts: raw GPU text, structured GPU JSON, structured machine JSON, and raw machine text. In its current form, the script writes those files to a hard-coded output directory, so it is primarily suited to environments where that storage path already exists. 

### Outputs
  - filesystem: four timestamped files written to the configured output directory
    - `gpu_info_<timestamp>.txt`
    - `gpu_info_<timestamp>.json`
    - `machine_info_<timestamp>.txt`
    - `machine_info_<timestamp>.json`
  - stdout: status messages showing where each artifact was saved

#### Example outputs
##### Machine information
###### `machine_info_2026-02FEB-15_00h15m31s--UTC.txt`
``` json
OAR_JOB_ID:               3489081
HOST_HOST_NAME:           abacus9-1.rennes.grid5000.fr
hostname:                 e13cf011a7d5

CPU Info:
Architecture:                x86_64
  CPU op-mode(s):            32-bit, 64-bit
  Address sizes:             46 bits physical, 48 bits virtual
  Byte Order:                Little Endian
CPU(s):                      40
  On-line CPU(s) list:       0-39
Vendor ID:                   GenuineIntel
  Model name:                Intel(R) Xeon(R) Silver 4114 CPU @ 2.20GHz
    CPU family:              6
    Model:                   85
    Thread(s) per core:      2
    Core(s) per socket:      10
    Socket(s):               2
    Stepping:                4
    CPU(s) scaling MHz:      60%
    CPU max MHz:             3000.0000
    CPU min MHz:             800.0000
    BogoMIPS:                4400.00
    Flags:                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx 
                             pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 
                             monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsav
                             e avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3 cdp_l3 invpcid_single pti intel_ppin ssbd mba ibrs ibpb stibp tp
                             r_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm mpx rdt_a avx512f avx51
                             2dq rdseed adx smap clflushopt clwb intel_pt avx512cd avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mb
                             m_total cqm_mbm_local dtherm ida arat pln pts hwp hwp_act_window hwp_epp hwp_pkg_req pku ospke md_clear flush_l1d arch_capabilities
                              ibpb_exit_to_user
Virtualization features:     
  Virtualization:            VT-x
Caches (sum of all):         
  L1d:                       640 KiB (20 instances)
  L1i:                       640 KiB (20 instances)
  L2:                        20 MiB (20 instances)
  L3:                        27.5 MiB (2 instances)
NUMA:                        
  NUMA node(s):              2
  NUMA node0 CPU(s):         0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38
  NUMA node1 CPU(s):         1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39
Vulnerabilities:             
  Gather data sampling:      Mitigation; Microcode
  Indirect target selection: Not affected
  Itlb multihit:             KVM: Mitigation: VMX disabled
  L1tf:                      Mitigation; PTE Inversion; VMX conditional cache flushes, SMT vulnerable
  Mds:                       Mitigation; Clear CPU buffers; SMT vulnerable
  Meltdown:                  Mitigation; PTI
  Mmio stale data:           Mitigation; Clear CPU buffers; SMT vulnerable
  Reg file data sampling:    Not affected
  Retbleed:                  Mitigation; IBRS
  Spec rstack overflow:      Not affected
  Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl and seccomp
  Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
  Spectre v2:                Mitigation; IBRS, IBPB conditional, STIBP conditional, RSB filling, PBRSB-eIBRS Not affected
  Srbds:                     Not affected
  Tsa:                       Not affected
  Tsx async abort:           Mitigation; Clear CPU buffers; SMT vulnerable
  Vmscape:                   Mitigation; IBPB before exit to userspace


GPU Info:
Sun Feb 15 00:15:32 2026       
+---------------------------------------------------------------------------------------+
| NVIDIA-SMI 535.183.06             Driver Version: 535.183.06   CUDA Version: 12.2     |
|-----------------------------------------+----------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |         Memory-Usage | GPU-Util  Compute M. |
|                                         |                      |               MIG M. |
|=========================================+======================+======================|
|   0  Tesla V100-SXM2-32GB           On  | 00000000:1A:00.0 Off |                    0 |
| N/A   40C    P0              43W / 300W |      0MiB / 32768MiB |      0%      Default |
|                                         |                      |                  N/A |
+-----------------------------------------+----------------------+----------------------+
|   1  Tesla V100-SXM2-32GB           On  | 00000000:1C:00.0 Off |                    0 |
| N/A   37C    P0              44W / 300W |      0MiB / 32768MiB |      0%      Default |
|                                         |                      |                  N/A |
+-----------------------------------------+----------------------+----------------------+
|   2  Tesla V100-SXM2-32GB           On  | 00000000:1D:00.0 Off |                    0 |
| N/A   33C    P0              42W / 300W |      0MiB / 32768MiB |      0%      Default |
|                                         |                      |                  N/A |
+-----------------------------------------+----------------------+----------------------+
|   3  Tesla V100-SXM2-32GB           On  | 00000000:1E:00.0 Off |                    0 |
| N/A   39C    P0              42W / 300W |      0MiB / 32768MiB |      0%      Default |
|                                         |                      |                  N/A |
+-----------------------------------------+----------------------+----------------------+
                                                                                         
+---------------------------------------------------------------------------------------+
| Processes:                                                                            |
|  GPU   GI   CI        PID   Type   Process name                            GPU Memory |
|        ID   ID                                                             Usage      |
|=======================================================================================|
|  No running processes found                                                           |
+---------------------------------------------------------------------------------------+
```

###### `machine_info_2026-02FEB-15_00h15m31s--UTC.json`
```json
{
  "job_id": "3489081",
  "host_hostname": "abacus9-1.rennes.grid5000.fr",
  "hostname": "e13cf011a7d5",
  "cpu_info": {
    "general": {
      "Architecture": "x86_64",
      "CPU op-mode(s)": "32-bit, 64-bit",
      "Address sizes": "46 bits physical, 48 bits virtual",
      "Byte Order": "Little Endian",
      "CPU(s)": "40",
      "On-line CPU(s) list": "0-39",
      "Vendor ID": "GenuineIntel",
      "Model name": "Intel(R) Xeon(R) Silver 4114 CPU @ 2.20GHz",
      "CPU family": "6",
      "Model": "85",
      "Thread(s) per core": "2",
      "Core(s) per socket": "10",
      "Socket(s)": "2",
      "Stepping": "4",
      "CPU(s) scaling MHz": "74%",
      "CPU max MHz": "3000.0000",
      "CPU min MHz": "800.0000",
      "BogoMIPS": "4400.00",
      "Flags": "fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3 cdp_l3 invpcid_single pti intel_ppin ssbd mba ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm mpx rdt_a avx512f avx512dq rdseed adx smap clflushopt clwb intel_pt avx512cd avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts hwp hwp_act_window hwp_epp hwp_pkg_req pku ospke md_clear flush_l1d arch_capabilities ibpb_exit_to_user",
      "Virtualization": "VT-x"
    },
    "cache": {
      "L1d cache": "640 KiB (20 instances)",
      "L1i cache": "640 KiB (20 instances)",
      "L2 cache": "20 MiB (20 instances)",
      "L3 cache": "27.5 MiB (2 instances)"
    },
    "numa": {
      "NUMA node(s)": "2",
      "NUMA node0 CPU(s)": "0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38",
      "NUMA node1 CPU(s)": "1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39"
    },
    "vulnerabilities": {
      "Gather data sampling": "Mitigation; Microcode",
      "Indirect target selection": "Not affected",
      "Itlb multihit": "KVM: Mitigation: VMX disabled",
      "L1tf": "Mitigation; PTE Inversion; VMX conditional cache flushes, SMT vulnerable",
      "Mds": "Mitigation; Clear CPU buffers; SMT vulnerable",
      "Meltdown": "Mitigation; PTI",
      "Mmio stale data": "Mitigation; Clear CPU buffers; SMT vulnerable",
      "Reg file data sampling": "Not affected",
      "Retbleed": "Mitigation; IBRS",
      "Spec rstack overflow": "Not affected",
      "Spec store bypass": "Mitigation; Speculative Store Bypass disabled via prctl and seccomp",
      "Spectre v1": "Mitigation; usercopy/swapgs barriers and __user pointer sanitization",
      "Spectre v2": "Mitigation; IBRS, IBPB conditional, STIBP conditional, RSB filling, PBRSB-eIBRS Not affected",
      "Srbds": "Not affected",
      "Tsa": "Not affected",
      "Tsx async abort": "Mitigation; Clear CPU buffers; SMT vulnerable",
      "Vmscape": "Mitigation; IBPB before exit to userspace"
    }
  },
  "gpu_info": {
    "gpu_0": {
      "name": "Tesla V100-SXM2-32GB",
      "memory_total_MB": 32768,
      "driver_version": "535.183.06"
    },
    "gpu_1": {
      "name": "Tesla V100-SXM2-32GB",
      "memory_total_MB": 32768,
      "driver_version": "535.183.06"
    },
    "gpu_2": {
      "name": "Tesla V100-SXM2-32GB",
      "memory_total_MB": 32768,
      "driver_version": "535.183.06"
    },
    "gpu_3": {
      "name": "Tesla V100-SXM2-32GB",
      "memory_total_MB": 32768,
      "driver_version": "535.183.06"
    }
  }
}
```

##### GPU information
###### `gpu_info_2026-02FEB-15_00h15m31s--UTC.txt`
```json
Sun Feb 15 00:15:31 2026       
+---------------------------------------------------------------------------------------+
| NVIDIA-SMI 535.183.06             Driver Version: 535.183.06   CUDA Version: 12.2     |
|-----------------------------------------+----------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |         Memory-Usage | GPU-Util  Compute M. |
|                                         |                      |               MIG M. |
|=========================================+======================+======================|
|   0  Tesla V100-SXM2-32GB           On  | 00000000:1A:00.0 Off |                    0 |
| N/A   40C    P0              43W / 300W |      0MiB / 32768MiB |      0%      Default |
|                                         |                      |                  N/A |
+-----------------------------------------+----------------------+----------------------+
|   1  Tesla V100-SXM2-32GB           On  | 00000000:1C:00.0 Off |                    0 |
| N/A   37C    P0              44W / 300W |      0MiB / 32768MiB |      0%      Default |
|                                         |                      |                  N/A |
+-----------------------------------------+----------------------+----------------------+
|   2  Tesla V100-SXM2-32GB           On  | 00000000:1D:00.0 Off |                    0 |
| N/A   33C    P0              42W / 300W |      0MiB / 32768MiB |      0%      Default |
|                                         |                      |                  N/A |
+-----------------------------------------+----------------------+----------------------+
|   3  Tesla V100-SXM2-32GB           On  | 00000000:1E:00.0 Off |                    0 |
| N/A   39C    P0              42W / 300W |      0MiB / 32768MiB |      0%      Default |
|                                         |                      |                  N/A |
+-----------------------------------------+----------------------+----------------------+
                                                                                         
+---------------------------------------------------------------------------------------+
| Processes:                                                                            |
|  GPU   GI   CI        PID   Type   Process name                            GPU Memory |
|        ID   ID                                                             Usage      |
|=======================================================================================|
|  No running processes found                                                           |
+---------------------------------------------------------------------------------------+
```

###### `gpu_info_2026-02FEB-15_00h15m31s--UTC.json`
```json
{
  "gpu_0": {
    "name": "Tesla V100-SXM2-32GB",
    "memory_total_MB": 32768,
    "driver_version": "535.183.06"
  },
  "gpu_1": {
    "name": "Tesla V100-SXM2-32GB",
    "memory_total_MB": 32768,
    "driver_version": "535.183.06"
  },
  "gpu_2": {
    "name": "Tesla V100-SXM2-32GB",
    "memory_total_MB": 32768,
    "driver_version": "535.183.06"
  },
  "gpu_3": {
    "name": "Tesla V100-SXM2-32GB",
    "memory_total_MB": 32768,
    "driver_version": "535.183.06"
  }
}
```

# References
1. <a id="ref-1"></a>https://oar.readthedocs.io/en/2.5/user/commands/oarstat.html
2. <a id="ref-2"></a>https://oar.imag.fr/
