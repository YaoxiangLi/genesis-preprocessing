# Bootstrap host environment

Observation date: 2026-10-07T16:09:02.473068+00:00. Workspace: `/home/exouser/projects/genesis-preprocessing-validation`. Upstream baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9` (`main`).

## Scope and acceptance

Bootstrap and read-only inventory only. No upstream source edits, checkout, dependency installation, image pull/build/push, workflow execution, sudo, or security/credential changes. Hostname is withheld because its sensitivity has not been established; the node field of `uname -a` is redacted. No environment-variable dump was taken.

**Bootstrap acceptance: PASS. Runtime readiness: INCOMPLETE.** Ubuntu 24.04.2 LTS, x86_64, 32 available logical CPUs (virtualized AMD EPYC-Milan), 123,626,663,936 bytes RAM (~115.14 GiB), and ~1.1 TiB available on the ext4 workspace filesystem. The filesystem is 88% occupied; workspace and `/tmp` share it. These are point-in-time observations, not reserved resources. Swap is 68,719,472,640 bytes.

Docker client and daemon both report 29.1.3. No configured workflow image is cached locally. Java is OpenJDK 21.0.12.1. PATH Python is Miniforge Python 3.12.12, not the project's pinned Python 3.14.5+gil. Pixi, Nextflow, uv, micromamba, Podman and Apptainer were not found on PATH. Absence from PATH does not prove absence everywhere on disk.

## Raw command observations

Commands ran from the workspace using the existing host tools. Each record preserves stdout and stderr separately, including successful version commands that write to stderr. `findmnt` output is reduced to unique filesystem types to avoid disclosing unrelated mount paths. Peak RAM was not instrumented per environment probe (UNAVAILABLE); elapsed times below are measured wall times. Host probe inputs are live OS state, so static input checksums are not applicable except `/etc/os-release`, recorded below.

`/etc/os-release` SHA256: `176275809152613bf71e86becb8e2d5f1ab006340b51bdbfef3625eff6c2f5f8`.

### `cat /etc/os-release`

Exit: 0; elapsed: 0.0032 seconds.

stdout:
```text
PRETTY_NAME="Ubuntu 24.04.2 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.2 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
```

stderr:
```text
(empty)
```

### `uname -a`

Exit: 0; elapsed: 0.0031 seconds.

stdout:
```text
Linux [hostname withheld] 6.17.0-35-generic #35~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue May 26 19:30:42 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
```

stderr:
```text
(empty)
```

### `uname -m`

Exit: 0; elapsed: 0.0029 seconds.

stdout:
```text
x86_64
```

stderr:
```text
(empty)
```

### `lscpu`

Exit: 0; elapsed: 0.0263 seconds.

stdout:
```text
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           40 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  32
On-line CPU(s) list:                     0-31
Vendor ID:                               AuthenticAMD
Model name:                              AMD EPYC-Milan Processor
CPU family:                              25
Model:                                   1
Thread(s) per core:                      1
Core(s) per socket:                      1
Socket(s):                               32
Stepping:                                1
BogoMIPS:                                3992.49
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm rep_good nopl xtopology cpuid extd_apicid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm cmp_legacy svm cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw topoext perfctr_core ssbd ibrs ibpb stibp vmmcall fsgsbase tsc_adjust bmi1 avx2 smep bmi2 invpcid rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 xsaves clzero xsaveerptr wbnoinvd arat npt lbrv nrip_save tsc_scale vmcb_clean flushbyasid pausefilter pfthreshold v_vmsave_vmload vgif umip pku ospke vaes vpclmulqdq rdpid arch_capabilities
Virtualization:                          AMD-V
Hypervisor vendor:                       KVM
Virtualization type:                     full
L1d cache:                               1 MiB (32 instances)
L1i cache:                               1 MiB (32 instances)
L2 cache:                                16 MiB (32 instances)
L3 cache:                                1 GiB (32 instances)
NUMA node(s):                            1
NUMA node0 CPU(s):                       0-31
Vulnerability Gather data sampling:      Not affected
Vulnerability Ghostwrite:                Not affected
Vulnerability Indirect target selection: Not affected
Vulnerability Itlb multihit:             Not affected
Vulnerability L1tf:                      Not affected
Vulnerability Mds:                       Not affected
Vulnerability Meltdown:                  Not affected
Vulnerability Mmio stale data:           Not affected
Vulnerability Old microcode:             Not affected
Vulnerability Reg file data sampling:    Not affected
Vulnerability Retbleed:                  Not affected
Vulnerability Spec rstack overflow:      Vulnerable: Safe RET, no microcode
Vulnerability Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl
Vulnerability Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:                Mitigation; Retpolines; IBPB conditional; IBRS_FW; STIBP disabled; RSB filling; PBRSB-eIBRS Not affected; BHI Not affected
Vulnerability Srbds:                     Not affected
Vulnerability Tsa:                       Vulnerable: No microcode
Vulnerability Tsx async abort:           Not affected
Vulnerability Vmscape:                   Not affected
```

stderr:
```text
(empty)
```

### `nproc`

Exit: 0; elapsed: 0.0057 seconds.

stdout:
```text
32
```

stderr:
```text
(empty)
```

### `nproc --all`

Exit: 0; elapsed: 0.0022 seconds.

stdout:
```text
32
```

stderr:
```text
(empty)
```

### `free -b`

Exit: 0; elapsed: 0.0038 seconds.

stdout:
```text
               total        used        free      shared  buff/cache   available
Mem:     123626663936  7984930816 92714414080    35880960 24163758080 115641733120
Swap:    68719472640           0 68719472640
```

stderr:
```text
(empty)
```

### `findmnt -rn -o FSTYPE`

Exit: 0; elapsed: 0.0038 seconds.

stdout:
```text
autofs
binfmt_misc
bpf
cgroup2
configfs
debugfs
devpts
devtmpfs
efivarfs
ext4
fuse.gvfsd-fuse
fuse.portal
fusectl
hugetlbfs
mqueue
nsfs
overlay
proc
pstore
securityfs
squashfs
sysfs
tmpfs
tracefs
vfat
```

stderr:
```text
(empty)
```

### `df -hT . /tmp`

Exit: 0; elapsed: 0.0028 seconds.

stdout:
```text
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/sda1      ext4  8.6T  7.5T  1.1T  88% /
/dev/sda1      ext4  8.6T  7.5T  1.1T  88% /
```

stderr:
```text
(empty)
```

### `bash -c 'printf "Configured shell: %s\n" "$SHELL"; ps -p $$ -o comm=; bash --version; ulimit -Sa; ulimit -Ha'`

Exit: 0; elapsed: 0.0497 seconds.

stdout:
```text
Configured shell: /bin/bash
bash
GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu)
Copyright (C) 2022 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>

This is free software; you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
real-time non-blocking time  (microseconds, -R) unlimited
core file size              (blocks, -c) 0
data seg size               (kbytes, -d) unlimited
scheduling priority                 (-e) 0
file size                   (blocks, -f) unlimited
pending signals                     (-i) 471079
max locked memory           (kbytes, -l) 15091144
max memory size             (kbytes, -m) unlimited
open files                          (-n) 1048576
pipe size                (512 bytes, -p) 8
POSIX message queues         (bytes, -q) 819200
real-time priority                  (-r) 0
stack size                  (kbytes, -s) 8192
cpu time                   (seconds, -t) unlimited
max user processes                  (-u) 471079
virtual memory              (kbytes, -v) unlimited
file locks                          (-x) unlimited
real-time non-blocking time  (microseconds, -R) unlimited
core file size              (blocks, -c) unlimited
data seg size               (kbytes, -d) unlimited
scheduling priority                 (-e) 0
file size                   (blocks, -f) unlimited
pending signals                     (-i) 471079
max locked memory           (kbytes, -l) 15091144
max memory size             (kbytes, -m) unlimited
open files                          (-n) 1048576
pipe size                (512 bytes, -p) 8
POSIX message queues         (bytes, -q) 819200
real-time priority                  (-r) 0
stack size                  (kbytes, -s) unlimited
cpu time                   (seconds, -t) unlimited
max user processes                  (-u) 471079
virtual memory              (kbytes, -v) unlimited
file locks                          (-x) unlimited
```

stderr:
```text
(empty)
```

### `git --version`

Exit: 0; elapsed: 0.0023 seconds.

stdout:
```text
git version 2.43.0
```

stderr:
```text
(empty)
```

### `curl --version`

Exit: 0; elapsed: 0.053 seconds.

stdout:
```text
curl 8.5.0 (x86_64-pc-linux-gnu) libcurl/8.5.0 OpenSSL/3.0.13 zlib/1.3 brotli/1.1.0 zstd/1.5.5 libidn2/2.3.7 libpsl/0.21.2 (+libidn2/2.3.7) libssh/0.10.6/openssl/zlib nghttp2/1.59.0 librtmp/2.3 OpenLDAP/2.6.7
Release-Date: 2023-12-06, security patched: 8.5.0-2ubuntu10.15
Protocols: dict file ftp ftps gopher gophers http https imap imaps ldap ldaps mqtt pop3 pop3s rtmp rtsp scp sftp smb smbs smtp smtps telnet tftp
Features: alt-svc AsynchDNS brotli GSS-API HSTS HTTP2 HTTPS-proxy IDN IPv6 Kerberos Largefile libz NTLM PSL SPNEGO SSL threadsafe TLS-SRP UnixSockets zstd
```

stderr:
```text
(empty)
```

### `wget --version`

Exit: 0; elapsed: 0.0089 seconds.

stdout:
```text
GNU Wget 1.21.4 built on linux-gnu.

-cares +digest -gpgme +https +ipv6 +iri +large-file -metalink +nls 
+ntlm +opie +psl +ssl/openssl 

Wgetrc: 
    /etc/wgetrc (system)
Locale: 
    /usr/share/locale 
Compile: 
    gcc -DHAVE_CONFIG_H -DSYSTEM_WGETRC="/etc/wgetrc" 
    -DLOCALEDIR="/usr/share/locale" -I. -I../../src -I../lib 
    -I../../lib -Wdate-time -D_FORTIFY_SOURCE=3 -DHAVE_LIBSSL -DNDEBUG 
    -g -O2 -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer 
    -ffile-prefix-map=/build/wget-JgCXcc/wget-1.21.4=. -flto=auto 
    -ffat-lto-objects -fstack-protector-strong -fstack-clash-protection 
    -Wformat -Werror=format-security -fcf-protection 
    -fdebug-prefix-map=/build/wget-JgCXcc/wget-1.21.4=/usr/src/wget-1.21.4-1ubuntu4.5 
    -DNO_SSLv2 -D_FILE_OFFSET_BITS=64 -g -Wall 
Link: 
    gcc -DHAVE_LIBSSL -DNDEBUG -g -O2 -fno-omit-frame-pointer 
    -mno-omit-leaf-frame-pointer 
    -ffile-prefix-map=/build/wget-JgCXcc/wget-1.21.4=. -flto=auto 
    -ffat-lto-objects -fstack-protector-strong -fstack-clash-protection 
    -Wformat -Werror=format-security -fcf-protection 
    -fdebug-prefix-map=/build/wget-JgCXcc/wget-1.21.4=/usr/src/wget-1.21.4-1ubuntu4.5 
    -DNO_SSLv2 -D_FILE_OFFSET_BITS=64 -g -Wall -Wl,-Bsymbolic-functions 
    -flto=auto -ffat-lto-objects -Wl,-z,relro -Wl,-z,now -lpcre2-8 
    -luuid -lidn2 -lssl -lcrypto -lz -lpsl ../lib/libgnu.a 

Copyright (C) 2015 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later
<http://www.gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Originally written by Hrvoje Niksic <hniksic@xemacs.org>.
Please send bug reports and questions to <bug-wget@gnu.org>.
```

stderr:
```text
(empty)
```

### `docker --version`

Exit: 0; elapsed: 0.0794 seconds.

stdout:
```text
Docker version 29.1.3, build 29.1.3-0ubuntu3~24.04.2
```

stderr:
```text
(empty)
```

### `docker version --format '{{.Server.Version}}'`

Exit: 0; elapsed: 0.0255 seconds.

stdout:
```text
29.1.3
```

stderr:
```text
(empty)
```

### `podman --version`

Exit: 127; elapsed: 0.0007 seconds.

stdout:
```text
(empty)
```

stderr:
```text
Executable not found on PATH```

### `apptainer --version`

Exit: 127; elapsed: 0.0005 seconds.

stdout:
```text
(empty)
```

stderr:
```text
Executable not found on PATH```

### `java -version`

Exit: 0; elapsed: 0.171 seconds.

stdout:
```text
(empty)
```

stderr:
```text
openjdk version "21.0.12.1" 2026-08-18
OpenJDK Runtime Environment (build 21.0.12.1+1-1-24.04.4-Ubuntu)
OpenJDK 64-Bit Server VM (build 21.0.12.1+1-1-24.04.4-Ubuntu, mixed mode, sharing)
```

### `pixi --version`

Exit: 127; elapsed: 0.0006 seconds.

stdout:
```text
(empty)
```

stderr:
```text
Executable not found on PATH```

### `python --version`

Exit: 0; elapsed: 0.0028 seconds.

stdout:
```text
Python 3.12.12
```

stderr:
```text
(empty)
```

### `python3 --version`

Exit: 0; elapsed: 0.0031 seconds.

stdout:
```text
Python 3.12.12
```

stderr:
```text
(empty)
```

### `nextflow -version`

Exit: 127; elapsed: 0.0006 seconds.

stdout:
```text
(empty)
```

stderr:
```text
Executable not found on PATH```

### `uv --version`

Exit: 127; elapsed: 0.0005 seconds.

stdout:
```text
(empty)
```

stderr:
```text
Executable not found on PATH```

### `micromamba --version`

Exit: 127; elapsed: 0.0005 seconds.

stdout:
```text
(empty)
```

stderr:
```text
Executable not found on PATH```

## Interpretation and unresolved prerequisites

- Install/select a pinned project-compatible Pixi distribution in a later environment-setup task, then use the existing lockfiles. No ad-hoc or system-wide install was attempted here.
- Root `pixi.lock` resolves Nextflow 25.10.4, uv 0.11.33, micromamba 2.5.0, ShellCheck 0.11.0 and OpenJDK 23.0.2 for linux-64. These are declared locked versions, **not installed/validated versions**. nf-schema 2.4.2 and nf-dotenv 1.0.0 must also be available. Offline tests assume cached Nextflow/plugins.
- `genesis_tools/.python-version` selects 3.14.5+gil; host Python 3.12.12 is only used for audit data collection with existing PyYAML 6.0.3 and standard-library modules. No project tests were run with this substitute interpreter.
- The five exact workflow image digests recorded in `01-repository-inventory.md` are absent locally. Registry access, image manifest architectures, tool versions inside images, and correspondence between images and this git SHA remain UNVERIFIED. No container was run.
- `repo/references/` is absent. Exact reference provenance and checksums, and public FASTQ checksums, must be established before scientific validation. The supplied Sorghum test sheet uses a different reference filename than the full Sorghum sheet; no substitution is authorized.
- No repository tags exist locally or in the remote tag listing. Build scripts call `git describe --tags --abbrev=0` before option handling; that command fails with exit 128. This blocks the documented build route and is recorded without a fix.
- Docker daemon access passed without permission changes. Apptainer/Podman are optional alternatives, not requirements for the observed `local,docker` profile.
- `lscpu` reports CPU vulnerability status, including “Vulnerable” entries; these are preserved as host observations. No security settings were changed. Shell limits are recorded above; there is no observed low open-file ceiling (soft/hard 1,048,576).

## Execution provenance

The clone command was `/usr/bin/time -v -o scratch/bootstrap-clone.time git clone https://github.com/kundajelab/genesis-preprocessing ./repo`, with stdout and stderr captured under `scratch/bootstrap-clone.*`. Exit 0; elapsed 0.53 seconds; peak RSS 18,912 KiB. No clone warnings/errors were emitted; stderr reports the destination.

Environment commands, exact outputs, return codes and per-command elapsed times are retained in `../scratch/bootstrap-environment.json`. Git probes are in `../scratch/bootstrap-git.json`; shell syntax and tag probes in `../scratch/bootstrap-checks.json`; lock/sheet parsing in `../scratch/bootstrap-locks-sheets.json`; local image inspection in `../scratch/bootstrap-images.json`. All refer to the baseline SHA above. Upstream input SHA256 values are in `../scratch/bootstrap-input-checksums.json` and the inventory appendix. Manual reading/report composition has no isolated CPU/RAM measurement; it must not be treated as a benchmark.

## Status

- Tested: host command availability/versions, Docker daemon query, filesystem/resources/limits, clone and remote identity, local image presence, shell syntax, lock parsing, module inventory, current-tree secret patterns and clean-tree checks.
- Passed: host capture and clone; Docker daemon access; 12/12 shell syntax checks; all five Pixi locks parse and all package records carry SHA256 values; current checkout matches remote HEAD/main; upstream remains clean.
- Failed/unavailable probes: six executables absent on PATH; five configured images missing locally; tag description exits 128. These are prerequisite findings, not a claim that the workflow was run and failed.
- Ambiguous: runtime correctness, biological validity, registry availability, image/source correspondence, real data/reference identity, and reproducibility are not established by bootstrap.
- Files changed: the upstream checkout was created, but none of its tracked files changed. Two audit Markdown reports and supporting `scratch/bootstrap-*` evidence were created outside `repo`; requested workspace directories were created. No validation implementation was added; no branch or commit was needed for a source change.

Final acceptance verification at 2026-10-07T16:15:47.175058+00:00: original repository file hashes unchanged; porcelain Git status empty (exit 0); both reports nonempty; all 12 module paths covered; requested directories present; vendored SPP hash matches the upstream test constant. Probe elapsed 0.0117 s; peak RAM not instrumented. Exact command and results: `../scratch/bootstrap-final-checks.json`.
