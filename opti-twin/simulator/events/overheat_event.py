"""Wall overheat event — ramps wall panel temp above 200°C threshold."""


def trigger_wall_overheat(machine) -> None:
    machine.inject_event("wall_overheat")
