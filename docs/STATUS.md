# Current baseline

Accepted release: **five-r5**, five games with Flappy touch, terminal-event
cleanup, variable pipe spacing and live distance. On 2026-11-16 the user reported
the real-camera test was perfect. No event trace or endurance duration was supplied.

Raw SHA256: `a3b5e0aa720f3703f6d3adcf771edb855ac99d63c24c116816976ff37c203ed8`.
Loaded extension: 232 KiB / 256 KiB; margin 24 KiB.

Local r5 evidence: 181 native touch events/replies/returned waits, 1,750 physics
cases, 26 render frames, seven GUI scenarios, 17 playability streams of 3,000
ticks, and 14 outside-game snapshots. The reorganized build must preserve the
raw hash; current reports live in `work/current-games`.

Only Flappy owns touch. Other games retain stock touch, which can leave Games.
Lift the finger before MENU. E147 controller emulation, touch recovery after
LCD/EVF switching, sustained stability and earlier rare R2 freezes remain open.
See [hardware review](HARDWARE_RISK_REVIEW.md).

r3 is withdrawn for a missing touch reply/deadlock. r4 repaired the reply but
missed over half of normal taps. r5 clears contact on release/tap/double-tap
endings (3/4/5). Preserve accepted packages and stock rollback unchanged.
