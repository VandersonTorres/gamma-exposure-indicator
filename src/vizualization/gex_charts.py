from decimal import Decimal
import matplotlib.pyplot as plt
import numpy as np


def plot_gex(total_gex_per_asset: dict, focus_ratio: float = 0.8):
    """
    Plot Gamma Exposure focused on most relevant strikes.

    Args:
        total_gex_per_asset: dict containing assets and gex per strikes
        focus_ratio: percentage of most relevant strikes (0.8 = 80% mais relevantes)
    """
    for asset, gex_data in total_gex_per_asset.items():
        name_parts = asset.split("_")
        date_part = name_parts[-1]
        asset_title = f"{name_parts[1].upper()} {name_parts[2].upper()} {date_part}"

        call_wall = gex_data.pop("call_wall")
        put_wall = gex_data.pop("put_wall")
        last_price = gex_data.pop("last_price")
        last_price = float(Decimal(last_price.replace(",", "")))

        # Sort strikes
        strikes = sorted([float(k) for k in gex_data.keys()])
        values = [gex_data[str(k)] for k in strikes]

        # Automatically calculates the width of the bar
        if len(strikes) > 1:
            step = min(np.diff(strikes))
            bar_width = step * 0.5
        else:
            bar_width = 1

        # At max 50 bars far of the last price
        if last_price in strikes:
            last_idx = strikes.index(last_price)
        else:
            last_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - last_price))

        min_idx = max(0, last_idx - 50)
        max_idx = min(len(strikes) - 1, last_idx + 50)

        strikes_focus = strikes[min_idx : max_idx + 1]
        values_focus = values[min_idx : max_idx + 1]

        # Criate Figure
        fig, ax = plt.subplots(figsize=(12, 6), dpi=120)

        # Bars: Blue for positive
        ax.bar(
            [s for s, v in zip(strikes_focus, values_focus) if v >= 0],
            [v for v in values_focus if v >= 0],
            width=bar_width,
            color="royalblue",
            alpha=0.7,
            label="Positive Gamma Exposure",
        )

        # Bars: Red for negative
        ax.bar(
            [s for s, v in zip(strikes_focus, values_focus) if v < 0],
            [v for v in values_focus if v < 0],
            width=bar_width,
            color="indianred",
            alpha=0.7,
            label="Negative Gamma Exposure",
        )

        # Find call wall strike
        call_wall_idx = values_focus.index(call_wall)
        call_wall_strike = strikes_focus[call_wall_idx]

        # Find put wall strike
        put_wall_idx = values_focus.index(put_wall)
        put_wall_strike = strikes_focus[put_wall_idx]

        # Call wall line
        ax.axvline(
            call_wall_strike,
            color="lightblue",
            linestyle="--",
            linewidth=1.2,
            label=f"Call Wall Strike: {call_wall_strike:.2f}",
        )
        ax.text(
            call_wall_strike,
            max(values_focus),
            f"Call Wall\n{call_wall_strike:.2f}",
            color="blue",
            fontsize=8,
            fontweight="bold",
            ha="left",
            va="bottom",
        )

        # Put wall line
        ax.axvline(
            put_wall_strike,
            color="pink",
            linestyle="--",
            linewidth=1.2,
            label=f"Put Wall Strike: {put_wall_strike:.2f}",
        )
        ax.text(
            put_wall_strike,
            min(values_focus),
            f"Put Wall\n{put_wall_strike:.2f}",
            color="purple",
            fontsize=8,
            fontweight="bold",
            ha="left",
            va="bottom",
        )

        # Zero Line
        ax.axhline(0, color="black", linewidth=0.8)

        # Last price line
        ax.axvline(last_price, color="lightgreen", linestyle="--", linewidth=1.5, label=f"Last Price: {last_price:.2f}")
        ax.text(
            last_price,
            max(values_focus),
            f"Last Price: {last_price:.2f}",
            color="green",
            fontsize=8,
            fontweight="bold",
            ha="left",
            va="bottom",
        )

        # Axios X zoom
        ax.set_xlim(strikes_focus[0], strikes_focus[-1])

        # shortest scale at Y Axios
        y_max = max(abs(v) for v in values_focus) * 1.2
        ax.set_ylim(-y_max, y_max)

        # Design
        ax.set_title(f"Gamma Exposure - {asset_title}", fontsize=16, fontweight="bold")
        ax.set_xlabel("Strike Price", fontsize=12)
        ax.set_ylabel("Gamma Exposure", fontsize=12, fontweight="bold")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.6)

        plt.tight_layout()
        plt.show()
