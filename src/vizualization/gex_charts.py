import matplotlib.pyplot as plt
import numpy as np


def plot_gex(total_gex_per_asset: dict, mode: str = "total"):
    """
    Plot Gamma Exposure focused on most relevant strikes.

    Args:
        total_gex_per_asset (dict): containing assets and gex per strikes
        mode (str): Options of plotting
            - total: aggregated exposure per strike
            - split: separate exposure for calls and puts
    """
    for asset, gex_data in total_gex_per_asset.items():
        name_parts = asset.split("_")
        date_part = name_parts[-1]
        asset_title = f"{name_parts[1].upper()} {name_parts[2].upper()} {date_part}"

        last_price = gex_data.pop("last_price")

        # Sort strikes
        strikes = sorted([float(k) for k in gex_data.keys()])
        if mode == "total":
            values = [gex_data[str(k)]["total"] for k in strikes]
        elif mode == "split":
            calls = [gex_data[str(k)]["call"] for k in strikes]
            puts = [gex_data[str(k)]["put"] for k in strikes]

        # Automatically calculates the width of the bar
        if len(strikes) > 1:
            step = min(np.diff(strikes))
            bar_width = step * 0.5
        else:
            bar_width = 1

        # At max 100 bars far of the last price
        if last_price in strikes:
            last_idx = strikes.index(last_price)
        else:
            last_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - last_price))
        min_idx = max(0, last_idx - 100)
        max_idx = min(len(strikes) - 1, last_idx + 100)
        strikes_focus = strikes[min_idx : max_idx + 1]

        # Criate Figure
        fig, ax = plt.subplots(figsize=(12, 6), dpi=120)

        # Bars: Blue for positive
        if mode == "total":
            values_focus = values[min_idx : max_idx + 1]
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
        elif mode == "split":
            ax.bar(strikes, calls, width=bar_width, color="royalblue", alpha=0.6, label="Calls Exposure")
            ax.bar(strikes, puts, width=bar_width, color="indianred", alpha=0.6, label="Puts Exposure")

            values_focus = [c + p for c, p in zip(calls, puts)][min_idx : max_idx + 1]

        if mode == "total":
            # Find call wall strike
            call_wall_idx = values_focus.index(max(values_focus))
            call_wall_strike = strikes_focus[call_wall_idx]

            # Find put wall strike
            put_wall_idx = values_focus.index(min(values_focus))
            put_wall_strike = strikes_focus[put_wall_idx]

            # Call wall line
            ax.axvline(
                call_wall_strike,
                color="lightblue",
                linestyle="--",
                linewidth=0.9,
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
                linewidth=0.9,
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
