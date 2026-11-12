**Status update:** [r2 on-camera validation passed](ON_CAMERA_VALIDATION_R2.md), as confirmed by the user after installation. Earlier pending-retest statements below describe the pre-confirmation state. Long-session and instrumented hardware checks remain unverified.

# Breakout r2 - buttons only

The user reported that the first four-game release mostly worked, but touch
failed and entering Breakout froze the camera. Root cause is not proven.
At their request, r2 removes the entire 0x9100 interception/payload-reading
path, gesture handler, drag anchors and touch HUD. Stock camera touch dispatch
is unchanged. Left/Right hold moves, OK serves one waiting ball, INFO restarts,
MENU returns to launcher, shutter/display exits cancel the shared timer.

The game retains 18 bricks, three lives and a 120ms tick. Tests cover native
rules, rendering sentinels, button-driven full clear/rally, touch pass-through
with no game action, restart, endings, cross-game transitions and exits.
Exact results are in release evidence; emulator success cannot confirm the
hardware freeze is fixed.

The stock Games title is replaced by a small padded 120x32 bitmap at (390,554),
below the playfield ending at y540, using the existing two-output paint hook.
This avoids the stock font box clipping. Screenshot review covers placement.

Release: om3-games-bundle-buttons-r2. See INSTALL_AND_RESTORE.md. No optional
film presets ship; the package still uses the pinned Caduceus baseline.

Stock touch handling can close Games during a swipe; that is expected in r2.
Use buttons for gameplay. The separate touch replay verifies timer cleanup.
