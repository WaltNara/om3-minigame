# Known issues

See [STATUS.md](STATUS.md) for the authoritative accepted release and hardware report.

- E147 physical touch-controller sequences are not emulated. r5 has a successful
  user-reported touch trial; no event trace or endurance duration was supplied.
- Touch recovery after LCD/EVF switching remains unverified. Teardown passes locally,
  but subsequent input also stalls with stock routing in the current harness.
- Earlier rare R2 boot/touch-exit freezes were not fully diagnosed; do not assume
  every such freeze had the same cause as r3's reproduced missing reply.
- Other games keep stock touch behavior, which can leave Games. Only Flappy owns
  touch; release the finger before MENU, following the stock held-touch policy.
- Current automated release gates focus on Flappy and integration/outside parity.
  They do not replace fresh per-game regressions when changing older games.

Resolved: 2048 uses INFO because Picture Mode does not deliver held-OK restart;
r3's touch deadlock was fixed by completing replies; r4 missed taps were fixed by
clearing contact on terminal kinds 3/4/5. Flappy remains slow with variable pipe
spacing and live distance.

[Earlier R2 findings](history/R2_KNOWN_ISSUES.md) remain historical evidence.
