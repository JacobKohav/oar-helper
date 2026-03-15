# oar-helper
OAR resource/task manager wrapper

What is OAR?
https://oar.imag.fr/
https://oar.readthedocs.io/en/2.5/user/commands/oarstat.html

# Problem Statement
Current OAR commands lack various functionalities: these library of scripts helps to remediate these gaps by adding onto existing OAR functions.

# Gaps identified
- single source of truth (SoT) job command 
- hardware specifications extraction

What is OAR?
https://oar.imag.fr/
https://oar.readthedocs.io/en/2.5/user/commands/oarstat.html

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
oar_jobs_summary.sh [user_name] [utc_offset]

Inputs:
  user_name: string, optional
    Target OAR username. Defaults to the current shell user.
  utc_offset: integer, optional
    UTC offset in hours used to render a localized scheduled-start column.
    Accepted forms include +2, -5, or 0.

Outputs:
  stdout: formatted job summary table
    Columns include job id, state, scheduled start, time until start,
    requested host, user, submission date, queue, walltime, GPU count,
    and raw UTC scheduled start.
  exit_behavior: shell-script execution
    Produces terminal-colored rows when `tput` is available.
```

### How it works
The script starts from `oarstat -u` and filters the jobs belonging to a target user. For each job, it then queries `oarstat -fj <job_id>` to pull the richer per-job metadata that is not available in the base listing. From that detailed output, it extracts the requested host, walltime, GPU request, and scheduled start time.

It accepts either a username, a UTC offset, or both as positional arguments. If no username is provided, it defaults to the current shell user. If a UTC offset is provided, the script converts the scheduled start time from UTC into that offset and adds a second timestamp column for easier local interpretation. It also computes the remaining delay before the predicted start time, then formats everything into a fixed-width table.

### Example output
``` bash
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

Outputs:
  filesystem: four timestamped files written to the configured output directory
    gpu_info_<timestamp>.txt
    gpu_info_<timestamp>.json
    machine_info_<timestamp>.txt
    machine_info_<timestamp>.json
  stdout: status messages showing where each artifact was saved
```

### How it works
The script collects hardware information directly from system commands available on the allocated node. CPU information is gathered through `lscpu` and reorganized into grouped JSON sections such as general CPU data, cache data, NUMA data, and vulnerability data. GPU information is gathered through `nvidia-smi`, both as a raw command dump and as a structured list of GPU model names, memory totals, and driver version.

It then combines that hardware data with basic execution context from environment variables and `hostname`. At runtime, it writes four timestamped artifacts: raw GPU text, structured GPU JSON, structured machine JSON, and raw machine text. In its current form, the script writes those files to a hard-coded output directory, so it is primarily suited to environments where that storage path already exists. 
