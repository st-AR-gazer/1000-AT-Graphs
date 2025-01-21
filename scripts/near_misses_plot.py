import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.widgets import Slider, RadioButtons
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, '..', 'data')
sys.path.append(os.path.join(data_dir, '..'))

from data.states import colors, streamers

def generate_palette(base_rgb, n):
    lighten = tuple(min(1, c + 0.5) for c in base_rgb)
    darken  = tuple(max(0, c - 0.5) for c in base_rgb)
    cmap = mcolors.LinearSegmentedColormap.from_list('custom', [lighten, base_rgb, darken])
    return [cmap(i/(n-1)) for i in range(n)]

export_path = os.path.join(data_dir, 'export.json')
df = pd.read_json(export_path)
df['datetime'] = pd.to_datetime(df['datetime'])
df['day'] = df['datetime'].dt.date

initial_threshold = 10
current_streamer = "Lars"
sort_method = 'Datetime'

def filter_reverse_near_misses(threshold, aliases):
    df['pb_diff'] = df['atTime'] - df['pbBeforeFin']
    cond = (df['pb_diff'] >= 0) & (df['pb_diff'] <= threshold) & df['player'].isin(aliases)
    return df[cond]

def plot_bars(filtered_data):
    ax.clear()
    ax_top.clear()
    
    if filtered_data.empty:
        ax.set_title("No events found under current criteria")
        fig.canvas.draw_idle()
        return

    unique_days = sorted(filtered_data['day'].unique())
    if current_streamer != "Both":
        base_color = tuple(c/255 for c in colors[current_streamer])
        palette = generate_palette(base_color, len(unique_days))
        day_to_color = {day: col for day, col in zip(unique_days, palette)}
        bar_colors = [day_to_color[row.day] for _, row in filtered_data.iterrows()]
    else:
        def get_color(player):
            for norm, aliases in streamers.items():
                if player in aliases and norm in colors:
                    return tuple(c/255 for c in colors[norm])
            return (0.5,0.5,0.5)
        bar_colors = [get_color(row.player) for _, row in filtered_data.iterrows()]

    x = np.arange(len(filtered_data))
    heights = filtered_data['pb_diff'].values
    map_names = filtered_data['mapTitle'].values

    ax.bar(x, heights, color=bar_colors)
    ax.set_xticks(x)
    ax.set_xticklabels(map_names, rotation=90, fontsize=8)
    ax.set_xlim(-0.5, len(filtered_data)-0.5)
    ax.set_ylabel("PB Difference to AT (ms)")
    ax.set_xlabel("Map Title")
    ax.set_title(f"Near misses : {current_streamer}")

    if sort_method != 'FinalTime':
        days = filtered_data['day'].values
        day_boundaries = []
        day_labels = []
        if len(days) > 0:
            current_day = days[0]
            start_index = 0
            for i in range(1, len(days)):
                if days[i] != current_day:
                    midpoint = (start_index + i - 1) / 2
                    day_boundaries.append(midpoint)
                    day_labels.append(str(current_day))
                    current_day = days[i]
                    start_index = i
            midpoint = (start_index + len(days)-1) / 2
            day_boundaries.append(midpoint)
            day_labels.append(str(current_day))

        ax_top.set_xticks(day_boundaries)
        ax_top.set_xticklabels(day_labels, rotation=45, ha='right', fontsize=8)
        ax_top.set_xlim(ax.get_xlim())
    else:
        ax_top.set_xticks([])
        ax_top.set_xticklabels([])

    fig.canvas.draw_idle()

def update_plot(*args):
    thresh = int(threshold_slider.val)
    global sort_method
    if current_streamer == "Both":
        aliases = streamers["Lars"] + streamers["Scrapie"]
    else:
        aliases = streamers[current_streamer]
        
    filtered = filter_reverse_near_misses(thresh, aliases)
    
    if sort_method == 'FinalTime':
        filtered = filtered.sort_values('pb_diff')
    else:
        filtered = filtered.sort_values('datetime')
        
    plot_bars(filtered)

def streamer_radio_func(label):
    global current_streamer
    current_streamer = label
    update_plot()

def sort_radio_func(label):
    global sort_method
    sort_method = label
    update_plot()

fig, ax = plt.subplots(figsize=(12, 6))
plt.subplots_adjust(left=0.18, right=0.88, bottom=0.25)

ax_top = ax.twiny()

slider_ax = plt.axes([0.9, 0.25, 0.02, 0.65])
threshold_slider = Slider(
    slider_ax, 'Threshold', 0, 5000, valinit=initial_threshold,
    orientation='vertical', valstep=1
)

radio_ax = plt.axes([0.02, 0.55, 0.12, 0.1])
radio = RadioButtons(radio_ax, ('Lars', 'Scrapie', 'Both'))

sort_radio_ax = plt.axes([0.02, 0.35, 0.12, 0.1])
sort_radio = RadioButtons(sort_radio_ax, ('Datetime', 'FinalTime'))

threshold_slider.on_changed(update_plot)
radio.on_clicked(streamer_radio_func)
sort_radio.on_clicked(sort_radio_func)

update_plot()

plt.show()
