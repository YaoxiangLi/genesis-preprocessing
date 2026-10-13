# Installation validation — 10 October 2026

These records cover a fresh checkout of revision
`b04bee282870ada4dff69b96bdd0cb9796ebda60` on Linux. The installation reused
package caches and the existing Pixi executable.

| Check | Result | Record |
| --- | --- | --- |
| Install project environments | PASS, 4.646 s | [Installation log](install.log) |
| Initial checks | Help, doctor and offline tutorial passed; full suite failed during plugin lookup | [Initial log](initial-checks.log) |
| Full suite with verified plugin archives | PASS, 133.200 s | [Recovered checks](checks.log) |
| Offline tutorial | Two included datasets, six fixture review decisions | [Measurements and hashes](checks.json) |

The receipt retains exact commands, plugin and log hashes, and the original
temporary paths. Those paths identify the recorded run. For a new installation,
use the [contributor guide](../../../docs/development.md), including its plugin
recovery instructions. This test did not run scientific containers, SSH workers,
a live model service or a site scheduler.
