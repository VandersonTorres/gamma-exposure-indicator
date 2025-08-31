import matplotlib.pyplot as plt
import numpy as np
import os
import webbrowser
from copy import deepcopy


def process_metrics(total_gex_per_asset: dict, path_to_store: str, mode: str):
    """
    Plot Gamma Exposure focused on most relevant strikes.

    Args:
        total_gex_per_asset (dict): containing assets and gex per strikes.
        path_to_store (str): Path to save the charts.
        mode (str): Options of plotting
            - total: aggregated exposure per strike
            - split: separate exposure for calls and puts
    """
    gex_metrics = deepcopy(total_gex_per_asset)
    for asset, gex_data in total_gex_per_asset.items():
        name_parts = asset.split("_")
        date_part = name_parts[-1]
        asset_title = f"{name_parts[1].upper()} {name_parts[2].upper()} {date_part}"

        last_price = gex_data.pop("last_price")
        flip_point = gex_data.pop("flip")

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

        # At max 30 bars far of the last price
        if last_price in strikes:
            last_idx = strikes.index(last_price)
        else:
            last_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - last_price))
        min_idx = max(0, last_idx - 30)
        max_idx = min(len(strikes) - 1, last_idx + 30)
        strikes_focus = strikes[min_idx : max_idx + 1]

        # Criate Figure
        fig, ax = plt.subplots(figsize=(10, 5), dpi=120)

        # Plot axios info during hover
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.4),
            arrowprops=dict(arrowstyle="->"),
        )
        annot.set_visible(False)

        def update_annot(event):
            if event.inaxes == ax:
                idx = np.argmin(np.abs(strikes - event.xdata))
                x = strikes[idx]
                y = values[idx]

                annot.xy = (x, y)
                annot.set_text(f"Strike: {x:.2f}\nGamma: {y:.2f}")
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                annot.set_visible(False)

        if mode == "total":
            values_focus = values[min_idx : max_idx + 1]
            # Bars: Blue for positive
            bars_pos = ax.bar(
                [s for s, v in zip(strikes_focus, values_focus) if v >= 0],
                [v for v in values_focus if v >= 0],
                width=bar_width,
                color="royalblue",
                alpha=0.7,
                label="Positive Gamma Exposure",
            )

            # Bars: Red for negative
            bars_neg = ax.bar(
                [s for s, v in zip(strikes_focus, values_focus) if v < 0],
                [v for v in values_focus if v < 0],
                width=bar_width,
                color="indianred",
                alpha=0.7,
                label="Negative Gamma Exposure",
            )
        elif mode == "split":
            bars_pos = ax.bar(strikes, calls, width=bar_width, color="royalblue", alpha=0.6, label="Calls Exposure")
            bars_neg = ax.bar(strikes, puts, width=bar_width, color="indianred", alpha=0.6, label="Puts Exposure")

            values_focus = [c + p for c, p in zip(calls, puts)][min_idx : max_idx + 1]

        # Plot strike values above the bars
        ax.bar_label(
            bars_pos,
            labels=[f"{s:.2f}" for s, v in zip(strikes_focus, values_focus) if v >= 0],
            padding=2,
            fontsize=5,
            color="darkblue",
            rotation=90,
        )
        ax.bar_label(
            bars_neg,
            labels=[f"{s:.2f}" for s, v in zip(strikes_focus, values_focus) if v < 0],
            padding=2,
            fontsize=5,
            color="purple",
            rotation=90,
        )

        if mode == "total":
            # Find call wall strike
            call_wall_idx = values_focus.index(max(values_focus))
            call_wall_strike = strikes_focus[call_wall_idx]
            gex_metrics[asset]["call_wall_strike"] = call_wall_strike

            # Find put wall strike
            put_wall_idx = values_focus.index(min(values_focus))
            put_wall_strike = strikes_focus[put_wall_idx]
            gex_metrics[asset]["put_wall_strike"] = put_wall_strike

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
                fontsize=6,
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
                fontsize=6,
                fontweight="bold",
                ha="left",
                va="bottom",
            )

        # Plot Flip Point if it exists
        if flip_point:
            flip_point = float(flip_point)
            ax.axvline(
                x=flip_point, color="yellow", linestyle="--", linewidth=2, label=f"Gamma Flip ({flip_point:.2f})"
            )
            ax.text(
                flip_point,
                min(values_focus),
                f"Gamma Flip ({flip_point:.2f})",
                color="yellow",
                fontsize=6,
                fontweight="bold",
                ha="left",
                va="bottom",
            )
            gex_metrics[asset]["flip_point"] = flip_point

        # === Detach top 4 positives ===
        top_calls = []
        pos_values = [bar.get_height() for bar in bars_pos]
        if pos_values:
            top_pos_idx = np.argsort(pos_values)[-4:]
            # Sort from highest to lowest
            top_pos_idx = sorted(top_pos_idx, key=lambda i: pos_values[i], reverse=True)
            for i in top_pos_idx:
                # Rounds to the closest 5 multiple
                call = round(bars_pos[i].get_x() / 5) * 5
                top_calls.append(call)
                bars_pos[i].set_color("darkblue")
        top_calls = ", ".join([str(call) for call in top_calls][1:])
        gex_metrics[asset]["top_calls"] = top_calls

        # === Detach top 4 negatives ===
        top_puts = []
        neg_values = [bar.get_height() for bar in bars_neg]
        if neg_values:
            top_neg_idx = np.argsort(neg_values)[:4]
            # Sort from highest to lowest
            top_neg_idx = sorted(top_neg_idx, key=lambda i: neg_values[i], reverse=False)
            for i in top_neg_idx:
                # Rounds to the closest 5 multiple
                put = round(bars_neg[i].get_x() / 5) * 5
                top_puts.append(put)
                bars_neg[i].set_color("darkred")
        top_puts = ", ".join([str(put) for put in top_puts][1:])
        gex_metrics[asset]["top_puts"] = top_puts

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
            ha="right",
            va="top",
        )

        # Axios X zoom
        ax.set_xlim(strikes_focus[0], strikes_focus[-1])

        # shortest scale at Y Axios
        y_max = max(abs(v) for v in values_focus) * 1.2
        ax.set_ylim(-y_max, y_max)

        # Design
        ax.set_title(f"Gamma Exposure - {asset_title}", fontsize=16, fontweight="bold")
        ax.set_xlabel("Strike Price", fontsize=12, fontweight="bold")
        ax.set_ylabel("Gamma Exposure", fontsize=12, fontweight="bold")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.6)

        fig.canvas.mpl_connect("motion_notify_event", update_annot)
        plt.tight_layout()

        # Save the chart
        filename = os.path.join(path_to_store, f"gex_{asset_title.lower().replace(' ', '_')}.png")
        gex_metrics[asset]["chart_image_path"] = filename
        fig.savefig(filename, dpi=150, bbox_inches="tight")

        # Show the charts into a webbrowser window
        webbrowser.open("file://" + os.path.abspath(filename))

        # Close the fig
        plt.close(fig)

    return gex_metrics
