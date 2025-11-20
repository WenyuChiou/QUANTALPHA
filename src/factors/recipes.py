"""Pre-built factor templates (TSMOM, low-vol, vol-scaled momentum)."""

from ..memory.factor_registry import FactorSpec, SignalSpec, PortfolioSpec, ValidationSpec, TargetsSpec


def get_tsmom_factor() -> FactorSpec:
    """Time-series momentum factor (12m - 1m returns)."""
    return FactorSpec(
        name="TSMOM_252_minus_21_volTarget",
        universe="sp500",
        frequency="D",
        signals=[
            SignalSpec(
                id="mom_long",
                expr="RET_LAG(1,252) - RET_LAG(1,21)",  # 12m - 1m
                normalize="zscore_252"
            ),
            SignalSpec(
                id="vol",
                expr="ROLL_STD(RET_D, 21)"
            ),
            SignalSpec(
                id="risk_target",
                expr="VOL_TARGET(ann_vol=0.15, using='vol')"
            )
        ],
        portfolio=PortfolioSpec(
            scheme="long_short_deciles",
            weight="equal",
            notional=1.0,
            costs={"bps_per_trade": 5, "borrow_bps": 50}
        ),
        validation=ValidationSpec(
            min_history_days=800,
            purge_gap_days=21,
            max_turnover_monthly=250.0
        ),
        targets=TargetsSpec(
            min_sharpe=1.0,
            max_maxdd=0.35,
            min_avg_ic=0.05
        )
    )


def get_low_vol_factor() -> FactorSpec:
    """Low volatility factor (inverse volatility)."""
    return FactorSpec(
        name="LowVol_InverseVol",
        universe="sp500",
        frequency="D",
        signals=[
            SignalSpec(
                id="inverse_vol",
                expr="1 / (ROLL_STD(RET_D, 21) + 0.001)",  # Inverse volatility
                normalize="zscore_252"
            )
        ],
        portfolio=PortfolioSpec(
            scheme="long_short_deciles",
            weight="equal",
            notional=1.0
        ),
        validation=ValidationSpec(
            min_history_days=800,
            purge_gap_days=21,
            max_turnover_monthly=200.0
        ),
        targets=TargetsSpec(
            min_sharpe=1.0,
            max_maxdd=0.30,
            min_avg_ic=0.04
        )
    )


def get_vol_scaled_momentum_factor() -> FactorSpec:
    """Volatility-scaled momentum factor."""
    return FactorSpec(
        name="VolScaledMOM_126_21",
        universe="sp500",
        frequency="D",
        signals=[
            SignalSpec(
                id="momentum",
                expr="RET_LAG(1,126) - RET_LAG(1,21)",  # 6m - 1m momentum
                normalize=None
            ),
            SignalSpec(
                id="volatility",
                expr="ROLL_STD(RET_D, 21)",
                normalize=None
            ),
            SignalSpec(
                id="vol_scaled_mom",
                expr="momentum / (volatility + 0.001)",  # Scale by volatility
                normalize="zscore_252"
            )
        ],
        portfolio=PortfolioSpec(
            scheme="long_short_deciles",
            weight="score_weighted",
            notional=1.0
        ),
        validation=ValidationSpec(
            min_history_days=800,
            purge_gap_days=21,
            max_turnover_monthly=250.0
        ),
        targets=TargetsSpec(
            min_sharpe=1.2,
            max_maxdd=0.35,
            min_avg_ic=0.06
        )
    )


def get_all_recipes() -> dict:
    """Get all pre-built factor recipes."""
    return {
        "tsmom": get_tsmom_factor(),
        "low_vol": get_low_vol_factor(),
        "vol_scaled_momentum": get_vol_scaled_momentum_factor()
    }

