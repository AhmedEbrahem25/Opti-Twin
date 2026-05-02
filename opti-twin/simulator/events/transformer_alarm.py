"""Transformer alarm — anchored to Nov 2024 EAF #2 transformer failure (Source: GEM)."""


def trigger_transformer_alarm(machine) -> None:
    machine.inject_event("transformer_alarm")
