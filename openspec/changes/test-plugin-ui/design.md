# Design: plugin UI walk

## Choice: parse QML accessibles, do not embed Quickshell

Alternative: boot a nested Hyprland and `omarchy plugin add` the example.

Reason: this environment has no Quickshell. The shell contract is still testable: manifest validation matches `omarchy plugin validate`, and panel entry points expose `open()` / `close()`. Accessible.name is what AT-SPI will see later.

Revisit when: a machine with Omarchy can run the `@future` summon scenario. Bead already lists the nested seat.

## Choice: one example plugin, two kinds

Bar widget summons, panel holds Refresh and Close. That is the smallest UI that is actually a plugin rather than a fake window.
