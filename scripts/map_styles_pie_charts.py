import sys, os, random, re
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, Slider, Button

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, '..', 'data')
export_file = os.path.join(data_dir, 'export.json')
sys.path.append(data_dir)

from states import streamers, colors
from tag_colors import tag_colors

df = pd.read_json(export_file)
df['styles'] = df['styles'].fillna('')

df_lars = df[df['player'].isin(streamers.get('Lars', []))]
df_scrapie = df[df['player'].isin(streamers.get('Scrapie', []))]

default_cutoff_percent = 0.03
view_mode = 'Pie Chart'
streamer_focus = 'Both'
days_mode = 'All Days'
chart_text_size = 10
chart_text_farawayness = 1.0

def tuple_to_hex(color_tuple):
    return '#{:02x}{:02x}{:02x}'.format(*color_tuple)

def get_color(style, base_color):
    if tag_colors.get(style):
        c = tag_colors[style]
        if len(c) == 6 and all(ch in '0123456789ABCDEFabcdef' for ch in c):
            return '#' + c
        return c
    random.seed(hash(style))
    r = int(base_color[1:3], 16) + random.randint(-20, 20)
    g = int(base_color[3:5], 16) + random.randint(-20, 20)
    b = int(base_color[5:7], 16) + random.randint(-20, 20)
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b))
    )

def calc_counts(df_x, mode):
    counts = Counter()
    if mode == 'Most':
        for styles in df_x['styles']:
            counts.update([s.strip() for s in styles.split(',') if s.strip()])
    elif mode.startswith('Best'):
        medal_type = 'at' if 'at' in mode else 'gold'
        df_medal = df_x[df_x['medal'] == medal_type]
        for styles in df_medal['styles']:
            counts.update([s.strip() for s in styles.split(',') if s.strip()])
    elif mode == 'Worst [skips]':
        for _, row in df_x.iterrows():
            skip = row.get('freeSkipCount', 0)
            styles = [s.strip() for s in row['styles'].split(',') if s.strip()]
            for style in styles:
                counts[style] += skip
    return dict(counts)

def group_small_styles(counts, cutoff):
    total = sum(counts.values())
    new_counts = {}
    other_total = 0
    for k, v in counts.items():
        ratio = v / total if total > 0 else 0
        if ratio < cutoff:
            other_total += v
        else:
            new_counts[k] = v
    return new_counts, other_total

def make_autopct(labels, total_counts, total_overall, other_total):
    def autopct(pct):
        autopct.counter += 1
        label = labels[autopct.counter - 1]
        if label == "Other":
            overall_pct = (other_total / total_overall) * 100 if total_overall > 0 else 0
            return f"{pct:.1f}% ({overall_pct:.1f}%)"
        overall_pct = (total_counts.get(label, 0) / total_overall) * 100 if total_overall > 0 else 0
        return f"{pct:.1f}% ({overall_pct:.1f}%)"
    autopct.counter = 0
    return autopct

def build_pie(ax, state):
    ax.clear()
    counts, other = state.get_current_counts()
    sorted_data = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k, _ in sorted_data]
    sizes = [v for _, v in sorted_data]
    if other > 0:
        labels.append("Other")
        sizes.append(other)
    if "Other" in labels:
        idx = labels.index("Other")
        labels.append(labels.pop(idx))
        sizes.append(sizes.pop(idx))
    colors_list = [get_color(label, state.base_color) for label in labels]
    total_overall = sum(state.total_counts.values())
    autopct_func = make_autopct(labels, state.total_counts, total_overall, other)
    patches, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct=autopct_func,
        startangle=90,
        pctdistance=0.8 * chart_text_farawayness,
        labeldistance=1.1 * chart_text_farawayness,
        colors=colors_list
    )
    ax.set_title(f"{state.label} (Iter {state.iteration}) - {state.order_mode}", fontsize=chart_text_size + 2)
    for i, wedge in enumerate(patches):
        if labels[i] == "Other":
            autotexts[i].set_text('')
            wedge.set_picker(True)
    for text in texts + autotexts:
        text.set_fontsize(chart_text_size)
    return patches

def build_list(ax, state):
    ax.clear()
    counts, other = state.get_current_counts()
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    total = sum(state.total_counts.values())
    lines = []
    for style, count in sorted_items:
        overall_pct = (state.total_counts.get(style, 0) / total) * 100 if total > 0 else 0
        current_pct = (count / sum(counts.values()) * 100) if sum(counts.values()) > 0 else 0
        lines.append(f"{style}: {count} ({current_pct:.1f}%) ({overall_pct:.1f}%)")
    if other > 0:
        other_overall_pct = (other / total) * 100 if total > 0 else 0
        other_current_pct = (other / sum(counts.values()) * 100) if sum(counts.values()) > 0 else 0
        lines.append(f"Other: {other} ({other_current_pct:.1f}%) ({other_overall_pct:.1f}%)")
    max_lines = int((0.8 * iteration_slider_height))
    if len(lines) > max_lines:
        half = len(lines) // 2
        text1 = "\n".join(lines[:half])
        text2 = "\n".join(lines[half:])
        ax.text(0.3, 0.5, text1, ha='left', va='center', fontsize=chart_text_size)
        ax.text(0.7, 0.5, text2, ha='left', va='center', fontsize=chart_text_size)
    else:
        text = "\n".join(lines)
        ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=chart_text_size)
    ax.set_axis_off()

class PieState:
    def __init__(self, label, df_x, base_color, cutoff_slider_ax, iteration_slider_ax, redraw_callback):
        self.label = label
        self.df_x = df_x
        self.base_color = base_color
        self.order_mode = 'Most'
        self.cutoff = default_cutoff_percent
        self.iteration = 1
        self.iterations = []
        self.total_counts = {}
        self.redraw_callback = redraw_callback
        self.initializing = True
        self.create_cutoff_slider(cutoff_slider_ax)
        self.create_iteration_slider(iteration_slider_ax)
        self.reset_state()
        self.initializing = False

    def create_cutoff_slider(self, base_ax):
        self.cutoff_slider = Slider(
            base_ax,
            'Cutoff',
            1, 6, 
            valinit=self.cutoff * 100, 
            valstep=0.5,
            orientation='horizontal'
        )
        self.cutoff_slider.on_changed(self.update_cutoff)

    def create_iteration_slider(self, base_ax):
        global iteration_slider_height
        iteration_slider_height = base_ax.get_position().height
        self.iteration_slider = Slider(
            base_ax,
            'Iteration',
            1,
            1,
            valinit=1,
            valstep=1,
            orientation='vertical'
        )
        self.iteration_slider.on_changed(self.update_iteration)

    def reset_state(self):
        self.iteration = 1
        self.iterations = []
        self.cutoff = default_cutoff_percent
        self.cutoff_slider.set_val(self.cutoff * 100)
        self.total_counts = calc_counts(self.df_x, self.order_mode)
        self.calculate_iterations()
        if not self.initializing:
            self.redraw_callback()

    def calculate_iterations(self):
        self.iterations = []
        df_current = self.df_x
        max_iterations = 10
        for _ in range(max_iterations):
            counts = calc_counts(df_current, self.order_mode)
            grouped_counts, other = group_small_styles(counts, self.cutoff)
            subset_df = None
            if other > 0:
                pattern = '|'.join(map(re.escape, grouped_counts.keys()))
                subset_df = df_current[~df_current['styles'].str.contains(pattern, regex=True)]
                if subset_df.empty:
                    self.iterations.append({'counts': grouped_counts, 'other': other, 'subset_df': subset_df})
                    break
                self.iterations.append({'counts': grouped_counts, 'other': other, 'subset_df': subset_df})
                df_current = subset_df
            else:
                self.iterations.append({'counts': grouped_counts, 'other': other, 'subset_df': subset_df})
                break
        self.iteration_slider.valmax = len(self.iterations)
        self.iteration_slider.ax.set_ylim(1, len(self.iterations))
        self.iteration_slider.set_val(1)
        self.iteration = 1

    def set_mode(self, mode):
        self.order_mode = mode
        self.reset_state()

    def set_cutoff(self, cutoff):
        self.cutoff = cutoff
        self.reset_state()

    def drill_down(self):
        if self.iteration < len(self.iterations):
            self.iteration += 1
            self.iteration_slider.set_val(self.iteration)
            self.redraw_callback()

    def update_cutoff(self, val):
        if self.initializing:
            return
        if view_mode == 'Pie Chart':
            self.cutoff = val / 100.0
        else:
            self.cutoff = val / 100.0
        self.calculate_iterations()
        self.iteration_slider.set_val(1)
        self.iteration = 1
        self.redraw_callback()

    def update_iteration(self, val):
        if self.initializing:
            return
        new_iter = int(val)
        if new_iter < 1:
            new_iter = 1
        elif new_iter > len(self.iterations):
            new_iter = len(self.iterations)
        self.iteration = new_iter
        self.redraw_callback()

    def get_current_counts(self):
        if self.iteration - 1 < len(self.iterations):
            return self.iterations[self.iteration - 1]['counts'], self.iterations[self.iteration - 1]['other']
        return {}, 0

    def get_subset_df(self):
        if self.iteration - 1 < len(self.iterations):
            return self.iterations[self.iteration - 1]['subset_df']
        return None

def redraw_charts():
    pie_ax_lars.clear()
    pie_ax_scrapie.clear()
    if view_mode == 'Pie Chart':
        if streamer_focus in ['Both', 'Lars']:
            build_pie(pie_ax_lars, state_lars)
            pie_ax_lars.set_visible(True)
        else:
            pie_ax_lars.set_visible(False)
        if streamer_focus in ['Both', 'Scrapie']:
            build_pie(pie_ax_scrapie, state_scrapie)
            pie_ax_scrapie.set_visible(True)
        else:
            pie_ax_scrapie.set_visible(False)
    else:
        if streamer_focus in ['Both', 'Lars']:
            build_list(pie_ax_lars, state_lars)
            pie_ax_lars.set_visible(True)
        else:
            pie_ax_lars.set_visible(False)
        if streamer_focus in ['Both', 'Scrapie']:
            build_list(pie_ax_scrapie, state_scrapie)
            pie_ax_scrapie.set_visible(True)
        else:
            pie_ax_scrapie.set_visible(False)
    fig.canvas.draw_idle()

def on_pick(event):
    wedge = event.artist
    label = wedge.get_label()
    if label == "Other":
        if wedge.axes == pie_ax_lars and streamer_focus in ['Both', 'Lars']:
            state_lars.drill_down()
        elif wedge.axes == pie_ax_scrapie and streamer_focus in ['Both', 'Scrapie']:
            state_scrapie.drill_down()
        redraw_charts()

def update_order(label):
    state_lars.set_mode(label)
    state_scrapie.set_mode(label)
    redraw_charts()

def update_view(label):
    global view_mode
    view_mode = label
    if view_mode == 'Pie Chart':
        state_lars.cutoff_slider.ax.set_visible(True)
        state_scrapie.cutoff_slider.ax.set_visible(True)
        text_size_slider.ax.set_visible(True)
        text_far_slider.ax.set_visible(True)
        cutoff_slider_step = 0.5
        cutoff_slider_min = 1
        cutoff_slider_max = 6
    else:
        state_lars.cutoff_slider.ax.set_visible(True)
        state_scrapie.cutoff_slider.ax.set_visible(True)
        text_size_slider.ax.set_visible(True)
        text_far_slider.ax.set_visible(False)
        max_pct_lars = max(state_lars.total_counts.values()) / sum(state_lars.total_counts.values()) * 100 if sum(state_lars.total_counts.values()) > 0 else 100
        max_pct_scrapie = max(state_scrapie.total_counts.values()) / sum(state_scrapie.total_counts.values()) * 100 if sum(state_scrapie.total_counts.values()) > 0 else 100
        cutoff_slider_step = 0.1
        cutoff_slider_min = 0
        cutoff_slider_max = max(max_pct_lars, max_pct_scrapie)
        state_lars.cutoff_slider.valmin = cutoff_slider_min
        state_lars.cutoff_slider.valmax = cutoff_slider_max
        state_lars.cutoff_slider.valstep = cutoff_slider_step
        state_lars.cutoff_slider.set_val(0)
        state_scrapie.cutoff_slider.valmin = cutoff_slider_min
        state_scrapie.cutoff_slider.valmax = cutoff_slider_max
        state_scrapie.cutoff_slider.valstep = cutoff_slider_step
        state_scrapie.cutoff_slider.set_val(0)
    state_lars.cutoff_slider.ax.figure.canvas.draw_idle()
    state_scrapie.cutoff_slider.ax.figure.canvas.draw_idle()
    state_lars.reset_state()
    state_scrapie.reset_state()

def update_player(label):
    global streamer_focus
    streamer_focus = label
    redraw_charts()

def update_days(label):
    global days_mode
    days_mode = label
    redraw_charts()

def reset_button_callback(event):
    state_lars.reset_state()
    state_scrapie.reset_state()

def update_text_size(val):
    global chart_text_size
    chart_text_size = val
    redraw_charts()

def update_text_farawayness(val):
    global chart_text_farawayness
    chart_text_farawayness = val
    redraw_charts()

fig = plt.figure(figsize=(20, 12))
plt.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.02)

pie_ax_lars = fig.add_axes([0.1, 0.3, 0.35, 0.6])
pie_ax_scrapie = fig.add_axes([0.55, 0.3, 0.35, 0.6])

order_ax = fig.add_axes([0.1, 0.15, 0.15, 0.1])
order_radio = RadioButtons(order_ax, ('Most', 'Best [at]', 'Best [gold]', 'Worst [skips]'))

view_ax = fig.add_axes([0.3, 0.15, 0.15, 0.1])
view_radio = RadioButtons(view_ax, ('Pie Chart', 'Ordered List'))

player_ax = fig.add_axes([0.5, 0.15, 0.15, 0.1])
player_radio = RadioButtons(player_ax, ('Lars', 'Scrapie', 'Both'))

days_ax = fig.add_axes([0.7, 0.15, 0.2, 0.1])
days_radio = RadioButtons(days_ax, ('All Days', 'Individual Days'))

cutoff_ax_lars = fig.add_axes([0.1, 0.08, 0.35, 0.02])
cutoff_ax_scrapie = fig.add_axes([0.55, 0.08, 0.35, 0.02])

text_far_ax = fig.add_axes([0.1, 0.05, 0.35, 0.02])
text_far_slider = Slider(
    text_far_ax,
    'Text Farawayness',
    0.5, 1.5,
    valinit=chart_text_farawayness,
    valstep=0.1,
    orientation='horizontal'
)
text_far_slider.on_changed(update_text_farawayness)

text_size_ax = fig.add_axes([0.55, 0.05, 0.35, 0.02])
text_size_slider = Slider(
    text_size_ax,
    'Text Size',
    8, 20,
    valinit=chart_text_size,
    valstep=1,
    orientation='horizontal'
)
text_size_slider.on_changed(update_text_size)

iteration_ax_lars = fig.add_axes([0.08, 0.3, 0.02, 0.6])
iteration_ax_scrapie = fig.add_axes([0.93, 0.3, 0.02, 0.6])

reset_ax = fig.add_axes([0.8, 0.02, 0.1, 0.04])
reset_button = Button(reset_ax, 'Reset Iter', hovercolor='0.975')

state_lars = PieState(
    "Lars",
    df_lars,
    tuple_to_hex(colors['Lars']),
    cutoff_ax_lars,
    iteration_ax_lars,
    redraw_charts
)
state_scrapie = PieState(
    "Scrapie",
    df_scrapie,
    tuple_to_hex(colors['Scrapie']),
    cutoff_ax_scrapie,
    iteration_ax_scrapie,
    redraw_charts
)

order_radio.on_clicked(update_order)
view_radio.on_clicked(update_view)
player_radio.on_clicked(update_player)
days_radio.on_clicked(update_days)

reset_button.on_clicked(reset_button_callback)

fig.canvas.mpl_connect('pick_event', on_pick)

redraw_charts()
plt.show()
