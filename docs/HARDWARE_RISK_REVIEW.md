# Hardware risk and evidence

Current baseline is r5; the user reports a perfect camera touch test. That is a
successful trial, not a measured endurance/safety qualification. See [status](STATUS.md).

Installing modified firmware remains the largest irreversible risk. Use the exact
OM-3 1.1 / E147 target, full battery and separate verified stock rollback. Preserve
version-matched OM3MOD data. Follow [installation](INSTALL_FIVE_GAMES.md).

Games use fixed bounded buffers, no custom heap allocation, cancellable GUI
message timers and stale-generation checks. Touch must complete the camera reply
handshake; r3 missed this and deadlocked. r4 repaired it but left contact latched
on tap endings; r5 clears kinds 3/4/5. No game code mechanism for direct sensor,
lens or shutter damage was identified. These checks cannot prove hardware safety.

Remaining uncertainties: real graphics/DMA buffer timing, sustained temperature,
input latency under load, display-switch recovery and earlier rare R2 boot/exit
freezes. Do not increase frame rate or alter power/thermal/controller settings
without evidence. Exit Games when unused; existing camera sleep/protection stays
responsible for normal operation. A new freeze needs its own diagnosis.

Earlier detail is retained in [the R2 review](history/R2_HARDWARE_RISK_REVIEW.md),
which describes historical implementations and is not current validation.
