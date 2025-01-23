import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import random
from matplotlib.widgets import RadioButtons, Slider

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, '..', 'data')
sys.path.append(os.path.join(data_dir, '..'))

from data.states import colors, streamers

tag_colors = {
    "Race": "", "FullSpeed": "", "Tech": "", "RPG": "", "LOL": "", "Press Forward": "",
    "SpeedTech": "", "MultiLap": "", "Offroad": "705100", "Trial": "", "ZrT": "1a6300",
    "SpeedFun": "", "Competitive": "", "Ice": "05767d", "Dirt": "5e2d09", "Stunt": "",
    "Reactor": "d04500", "Platform": "", "Slow Motion": "004388", "Bumper": "aa0000",
    "Fragile": "993366", "Scenery": "", "Kacky": "", "Endurance": "", "Mini": "",
    "Remake": "", "Mixed": "", "Nascar": "", "SpeedDrift": "", "Minigame": "7e0e69",
    "Obstacle": "", "Transitional": "", "Grass": "06a805", "Backwards": "83aa00",
    "EngineOff": "f2384e", "Signature": "f1c438", "Royal": "ff0010", "Water": "69dbff",
    "Plastic": "fffc00", "Arena": "", "Freestyle": "", "Educational": "",
    "Sausage": "", "Bobsleigh": "", "Pathfinding": "", "FlagRush": "7a0000",
    "Puzzle": "459873", "Freeblocking": "ffffff", "Altered Nadeo": "3a3a3a",
    "SnowCar": "de4949", "Wood": "814b00", "Underwater": "03afff",
    "Turtle": "6bb74e", "RallyCar": "ff8c00", "MixedCar": "000000",
    "Bugslide": "4b7933", "Mudslide": "855925", "Moving Items": "e0dc82",
    "DesertCar": "f6ca4a", "SpeedMapping": "bd46b0", "NoBrake": "",
    "CruiseControl": "", "NoSteer": "", "RPG-Immersive": "", "Pipes": "",
    "Magnet": "", "NoGrip": ""
}

df = pd.read_json(os.path.join(data_dir, 'export.json'))
df['styles'] = df['styles'].fillna('')
df_lars = df[df['player'].isin(streamers.get("Lars", []))]
df_scrapie = df[df['player'].isin(streamers.get("Scrapie", []))]

def get_color(style):
    if style in tag_colors and tag_colors[style]:
        c = tag_colors[style]
        if len(c) == 6 and all(ch in '0123456789ABCDEFabcdef' for ch in c):
            return '#' + c
        return c
    random.seed(hash(style))
    return "#" + "".join(random.choice("0123456789ABCDEF") for _ in range(6))

def get_styles_counts(df_x):
    counts = {}
    for row in df_x['styles']:
        sp = [s.strip() for s in row.split(',') if s.strip()]
        for style in sp:
            counts[style] = counts.get(style, 0) + 1
    return counts

def get_styles_counts_golds(df_x):
    counts = {}
    df_gold = df_x[df_x['medal'] == 'gold']
    for row in df_gold['styles']:
        sp = [s.strip() for s in row.split(',') if s.strip()]
        for style in sp:
            counts[style] = counts.get(style, 0) + 1
    return counts

def get_styles_counts_ats(df_x):
    counts = {}
    df_at = df_x[df_x['medal'] == 'at']
    for row in df_at['styles']:
        sp = [s.strip() for s in row.split(',') if s.strip()]
        for style in sp:
            counts[style] = counts.get(style, 0) + 1
    return counts

def get_styles_counts_skips(df_x):
    counts = {}
    for idx, row in df_x.iterrows():
        sp = [s.strip() for s in row['styles'].split(',') if s.strip()]
        skip = row['freeSkipCount']
        for style in sp:
            counts[style] = counts.get(style, 0) + skip
    return counts

def calc_counts(df_x, mode):
    if mode == 'Most':
        return get_styles_counts(df_x)
    elif mode == 'Best':
        return get_styles_counts_ats(df_x)
    elif mode == 'Best [golds]':
        return get_styles_counts_golds(df_x)
    elif mode == 'Worst [skips]':
        return get_styles_counts_skips(df_x)
    return {}

def group_small_styles(counts):
    total = sum(counts.values())
    new_counts = {}
    other_total = 0
    for k, v in counts.items():
        if total == 0:
            new_counts[k] = v
        else:
            ratio = v / total
            if ratio < 0.02:
                other_total += v
            else:
                new_counts[k] = v
    return new_counts, other_total

class PieHistory:
    def __init__(self, label, df_x):
        self.label = label
        self.df_x = df_x
        self.order_mode = 'Most'
        self.stack = []
        self.create_initial()

    def create_initial(self):
        c = calc_counts(self.df_x, self.order_mode)
        c, o = group_small_styles(c)
        self.stack = [(c, o, 1)]

    def current(self):
        return self.stack[-1]

    def set_mode_and_reset(self, mode):
        self.order_mode = mode
        self.create_initial()

    def go_deeper(self):
        c, o, it = self.current()
        sub_counts = {}
        total = sum(c.values()) + o
        for k, v in c.items():
            if total > 0 and v / total < 0.02:
                sub_counts[k] = v
        if len(sub_counts) == 0:
            return
        self.stack.append((sub_counts, 0, it + 1))

    def go_up(self):
        if len(self.stack) > 1:
            self.stack.pop()

def build_pie(ax, state):
    c, o, it = state.current()
    ax.clear()
    data = dict(c)
    if o > 0:
        data["Other"] = o
    keys = list(data.keys())
    vals = [data[k] for k in keys]
    colors_list = [get_color(k) for k in keys]
    patches, texts, autotexts = ax.pie(vals, labels=keys, autopct='%1.1f%%', startangle=90, colors=colors_list)
    ax.set_title(f"{state.label} (iteration {it}): {state.order_mode}")
    for wedge in patches:
        wedge.set_picker(5)

def build_list(ax, state):
    c, o, it = state.current()
    ax.clear()
    sorted_vals = sorted(c.items(), key=lambda x: x[1], reverse=True)
    s = sum(c.values()) + o
    display_str = "\n".join([f"{k}: {v}" for k, v in sorted_vals])
    if o > 0:
        display_str += f"\nOther: {o}"
    if s == 0:
        ax.text(0.5, 0.5, f"{state.label} (iteration {it}): Empty", ha='center', va='center')
    else:
        ax.text(0.5, 0.5, f"{state.label} (iteration {it}):\n\n{display_str}", ha='center', va='center')

df_state_lars = PieHistory("Lars", df_lars)
df_state_scrapie = PieHistory("Scrapie", df_scrapie)

fig = plt.figure(figsize=(14, 9))
pie_ax_lars = fig.add_axes([0.05, 0.25, 0.38, 0.65])
pie_ax_scrapie = fig.add_axes([0.57, 0.25, 0.38, 0.65])

order_ax = fig.add_axes([0.05, 0.1, 0.25, 0.1])
order_radio = RadioButtons(order_ax, ('Most', 'Best', 'Best [golds]', 'Worst [skips]'))

list_ax = fig.add_axes([0.35, 0.1, 0.15, 0.1])
list_radio = RadioButtons(list_ax, ('Pie Chart', 'Ordered List'))

days_ax = fig.add_axes([0.52, 0.1, 0.2, 0.1])
days_radio = RadioButtons(days_ax, ('Single Chart', 'Show chart for individual days'))

slider_ax_lars = fig.add_axes([0.01, 0.25, 0.03, 0.65])
slider_ax_scrapie = fig.add_axes([0.53, 0.25, 0.03, 0.65])
slider_lars = Slider(slider_ax_lars, 'Iter L', 1, 1, valinit=1, valstep=1)
slider_scrapie = Slider(slider_ax_scrapie, 'Iter S', 1, 1, valinit=1, valstep=1)

chart_mode = 'Pie Chart'
days_mode = 'Single Chart'

def draw_charts():
    df_state_lars.set_mode_and_reset(df_state_lars.order_mode)
    df_state_scrapie.set_mode_and_reset(df_state_scrapie.order_mode)
    slider_lars.valmax = 1
    slider_scrapie.valmax = 1
    slider_lars.set_val(1)
    slider_scrapie.set_val(1)
    pie_ax_lars.clear()
    pie_ax_scrapie.clear()
    if days_mode == 'Single Chart':
        if chart_mode == 'Pie Chart':
            build_pie(pie_ax_lars, df_state_lars)
            build_pie(pie_ax_scrapie, df_state_scrapie)
        else:
            build_list(pie_ax_lars, df_state_lars)
            build_list(pie_ax_scrapie, df_state_scrapie)
    else:
        pie_ax_lars.text(0.5, 0.5, "14x2 day charts not implemented", ha='center', va='center')
        pie_ax_scrapie.text(0.5, 0.5, "14x2 day charts not implemented", ha='center', va='center')
    fig.canvas.draw_idle()

def order_radio_func(label):
    df_state_lars.set_mode_and_reset(label)
    df_state_scrapie.set_mode_and_reset(label)
    draw_charts()

def list_radio_func(label):
    global chart_mode
    chart_mode = label
    draw_charts()

def days_radio_func(label):
    global days_mode
    days_mode = label
    draw_charts()

def slider_lars_func(val):
    it = int(slider_lars.val)
    df_state_lars.set_mode_and_reset(df_state_lars.order_mode)
    for _ in range(it - 1):
        df_state_lars.go_deeper()
    if chart_mode == 'Pie Chart':
        build_pie(pie_ax_lars, df_state_lars)
    else:
        build_list(pie_ax_lars, df_state_lars)
    fig.canvas.draw_idle()

def slider_scrapie_func(val):
    it = int(slider_scrapie.val)
    df_state_scrapie.set_mode_and_reset(df_state_scrapie.order_mode)
    for _ in range(it - 1):
        df_state_scrapie.go_deeper()
    if chart_mode == 'Pie Chart':
        build_pie(pie_ax_scrapie, df_state_scrapie)
    else:
        build_list(pie_ax_scrapie, df_state_scrapie)
    fig.canvas.draw_idle()

order_radio.on_clicked(order_radio_func)
list_radio.on_clicked(list_radio_func)
days_radio.on_clicked(days_radio_func)
slider_lars.on_changed(slider_lars_func)
slider_scrapie.on_changed(slider_scrapie_func)

def on_pick(event):
    wedge = event.artist
    label = wedge.get_label()
    if label == "Other":
        if wedge.axes == pie_ax_lars:
            df_state_lars.go_deeper()
            build_pie(pie_ax_lars, df_state_lars)
        elif wedge.axes == pie_ax_scrapie:
            df_state_scrapie.go_deeper()
            build_pie(pie_ax_scrapie, df_state_scrapie)
        fig.canvas.draw_idle()

order_radio.on_clicked(order_radio_func)
list_radio.on_clicked(list_radio_func)
days_radio.on_clicked(days_radio_func)
fig.canvas.mpl_connect('pick_event', on_pick)

draw_charts()
plt.show()
