"""Electrode break event — spikes electrode consumption rate."""


def trigger_electrode_break(machine) -> None:
    machine.inject_event("electrode_break")
