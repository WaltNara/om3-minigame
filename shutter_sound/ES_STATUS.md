# ES sound status on the OM-3

Use this diagnostic build if the first shot plays a custom sound and subsequent
shots are silent. Follow the firmware install steps in the included README. The
readout uses a few bytes of fixed RAM and writes no log files to the card.

1. Turn the camera on, select **5D** under **MENU → Setup → Information Record → ES sound**, and set the drive mode to **Silent Single**.
2. Take four photos about two seconds apart. Note which photos were audible.
3. Without restarting the camera or changing the sound, highlight **ES sound** again. Press **INFO** once and photograph the four rows. Press **INFO** again to return to the regular settings.

The three columns in each row follow the order of the labels. Values are hexadecimal.

| Row | Values |
| --- | --- |
| Cap / Post / HLS | Capture hook entries, successful worker notifications, and observed `0x88` shooting callbacks |
| Wake / Ask / Open | Worker wakes with the exposure flag, custom sound requests, and opened custom players |
| Close / Drive / Gate | Player close calls returned, last drive value read, and last worker gate reached |
| Busy / Play / TX | Native UI player busy state, native audio play count, and copy/TX flags at the time the menu opened |

`Drive` is `1E` for Silent Single and `20` for Silent Sequential. `Gate` is
`01` for the stock queue, `02` for an unsupported drive mode, `03` for the
active custom copy path, `04` for the native UI player, `05` for the other
native UI audio owner, `06` for the native play count, `07` for an unavailable
SD WAV or inactive selection, and `08` for an attempted request. `TX` bits
are `1` for the custom copy, `2` for the native TX owner, `4` for the native
TX sequence, and `8` for a close in progress. Counters wrap after 255.

For spaced single shots, compare `Cap`, `Post`, and `Wake` first. A stalled
`Cap` with an increasing `HLS` points to the capture hook. A stalled `Wake`
with `Post` still increasing points to notification delivery or a blocked
worker. If `Wake` keeps increasing, compare `Ask` with `Open` to see whether
the player accepted each request. `Close` and the last row show whether the
previous player released its resources.

To rebuild this image from the repository, run
`py -3 build/extras.py all --diagnostics`. The ordinary build uses the same
command without `--diagnostics`.
