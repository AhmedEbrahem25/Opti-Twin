"""M2 tariff/load forecaster (planing-v2.md §6)."""

from .lstm_forecaster import (  # noqa: F401
    FORECAST_HORIZON,
    LOOKBACK,
    OBS_SUMMARY_DIM,
    QUANTILES,
    Forecaster,
    TariffLoadForecaster,
    load_forecaster,
    summarise_for_obs,
)
