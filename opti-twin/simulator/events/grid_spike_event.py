"""Grid spike event — Hz dip forces safe-power mode."""


def trigger_grid_spike(machine) -> None:
    machine.inject_event("grid_spike")
