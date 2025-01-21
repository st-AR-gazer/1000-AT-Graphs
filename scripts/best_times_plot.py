import sys, os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, TextBox
from matplotlib.ticker import FuncFormatter
from datetime import timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, '..', 'data')
sys.path.append(os.path.join(data_dir, '..'))

from data.states import colors, streamers

df = pd.read_json(os.path.join(data_dir, 'export.json'))
df['datetime'] = pd.to_datetime(df['datetime'])
df_at = df[df['medal'] == 'at'].sort_values('datetime').reset_index(drop=True)

mode = 'Single'
active_streamer = 'Lars'
duration = 10

def find_best_stretch(alias_list, dur):
    tmp = df_at[df_at['player'].isin(alias_list)].copy()
    if tmp.empty:
        return tmp
    tmp.reset_index(drop=True, inplace=True)
    best_start = best_end = 0
    best_count = 0
    start_idx = 0
    for end_idx in range(len(tmp)):
        window_start = tmp.loc[end_idx, 'datetime'] - timedelta(minutes=dur)
        while tmp.loc[start_idx, 'datetime'] < window_start:
            start_idx += 1
            if start_idx > end_idx:
                break
        count = end_idx - start_idx + 1
        if count > best_count:
            best_count = count
            best_start, best_end = start_idx, end_idx
    return tmp.loc[best_start:best_end]

def overlay_data(st1, st2, dur):
    d1 = find_best_stretch(streamers[st1], dur).copy()
    d2 = find_best_stretch(streamers[st2], dur).copy()
    if not d1.empty:
        d1.reset_index(drop=True, inplace=True)
        s1 = d1['datetime'].iloc[0]
        d1['offset_min'] = (d1['datetime'] - s1).dt.total_seconds() / 60
        d1['whichstreamer'] = st1
    if not d2.empty:
        d2.reset_index(drop=True, inplace=True)
        s2 = d2['datetime'].iloc[0]
        d2['offset_min'] = (d2['datetime'] - s2).dt.total_seconds() / 60
        d2['whichstreamer'] = st2
    c = pd.concat([d1, d2]).reset_index(drop=True)
    return c, d1, d2

fig, ax = plt.subplots(figsize=(9, 6))
plt.subplots_adjust(left=0.25, bottom=0.25, top=0.88)
ax_top = ax.twiny()

def minute_second_formatter(x, pos):
    return f"{x:.2f} ({int(x*60)})"

ax.set_ylabel("Time (min (sec))")
ax_top.set_xlabel("Time offset (minutes)")
ax.yaxis.set_major_formatter(FuncFormatter(minute_second_formatter))

def update_plot():
    ax.clear()
    ax_top.clear()
    ax.set_ylabel("Time (min (sec))")
    ax_top.set_xlabel("Time offset (minutes)")
    global mode, active_streamer, duration
    if mode == 'Single' and active_streamer == 'Both':
        active_streamer = 'Lars'
    if mode == 'Single':
        if active_streamer not in ('Lars', 'Scrapie'):
            active_streamer = 'Lars'
        d = find_best_stretch(streamers[active_streamer], duration).copy()
        if d.empty:
            ax.set_title("No data", pad=20)
            fig.canvas.draw_idle()
            return
        d.reset_index(drop=True, inplace=True)
        d['whichstreamer'] = active_streamer
        s = d['datetime'].iloc[0]
        d['offset_min'] = (d['datetime'] - s).dt.total_seconds()/60
        ax.set_title(f"Best {duration}-min stretch ({active_streamer}) : {len(d)} ATs", pad=20)
        c = [x/255 for x in colors[active_streamer]]
        y_in_min = (d['timeSpent']/1000)/60
        ax.plot(d['offset_min'], y_in_min, marker='o', color=c)
        ax.set_xlim(d['offset_min'].min(), d['offset_min'].max())
        ax_top.set_xlim(d['offset_min'].min(), d['offset_min'].max())
        ax.set_xticks(d['offset_min'])
        ax_top.set_xticks(d['offset_min'])
        ax.set_xticklabels(d['mapTitle'], rotation=45, ha='right')
        ax_top.set_xticklabels([f"{v:.1f}" for v in d['offset_min']], rotation=45, ha='left')
        map_lbls = ax.get_xticklabels()
        top_lbls = ax_top.get_xticklabels()
        for lbl, (_, row) in zip(map_lbls, d.iterrows()):
            co = [cc/255 for cc in colors[row['whichstreamer']]]
            lbl.set_color(co)
        for lbl, (_, row) in zip(top_lbls, d.iterrows()):
            co = [cc/255 for cc in colors[row['whichstreamer']]]
            lbl.set_color(co)
    else:
        if active_streamer == 'Both':
            st1, st2 = 'Lars', 'Scrapie'
            alpha1, alpha2 = 1.0, 1.0
            tag = "(Both)"
        else:
            if active_streamer == 'Lars':
                st1, st2 = 'Lars', 'Scrapie'
                alpha1, alpha2 = 1.0, 0.3
            else:
                st1, st2 = 'Scrapie', 'Lars'
                alpha1, alpha2 = 1.0, 0.3
            tag = "(Overlay)"
        combined, d1, d2 = overlay_data(st1, st2, duration)
        ax.set_title(f"Best {duration}-min stretch {tag} : {len(combined)} ATs", pad=20)
        if combined.empty:
            ax.set_xlabel("Map Title")
            fig.canvas.draw_idle()
            return
        c1 = [x/255 for x in colors[st1]]
        c2 = [x/255 for x in colors[st2]]
        if not d1.empty:
            y_in_min_1 = (d1['timeSpent']/1000)/60
            ax.plot(d1['offset_min'], y_in_min_1, marker='o', color=c1, alpha=alpha1)
        if not d2.empty:
            y_in_min_2 = (d2['timeSpent']/1000)/60
            ax.plot(d2['offset_min'], y_in_min_2, marker='o', color=c2, alpha=alpha2)
        xmin = combined['offset_min'].min()
        xmax = combined['offset_min'].max()
        ax.set_xlim(xmin, xmax)
        ax_top.set_xlim(xmin, xmax)
        ax.set_xticks(combined['offset_min'])
        ax_top.set_xticks(combined['offset_min'])
        ax.set_xticklabels(combined['mapTitle'], rotation=45, ha='right')
        ax_top.set_xticklabels([f"{v:.1f}" for v in combined['offset_min']], rotation=45, ha='left')
        map_lbls = ax.get_xticklabels()
        top_lbls = ax_top.get_xticklabels()
        for lbl, (_, row) in zip(map_lbls, combined.iterrows()):
            co = [cc/255 for cc in colors[row['whichstreamer']]]
            lbl.set_color(co)
        for lbl, (_, row) in zip(top_lbls, combined.iterrows()):
            co = [cc/255 for cc in colors[row['whichstreamer']]]
            lbl.set_color(co)
    fig.canvas.draw_idle()

rax1 = plt.axes([0.02, 0.78, 0.15, 0.07])
radio1 = RadioButtons(rax1, ('Single','Overlay'), active=0)
def on_view_mode(label):
    global mode, active_streamer
    mode = label
    if mode == 'Single' and active_streamer == 'Both':
        active_streamer = 'Lars'
        radio2.set_active(0)
    update_plot()
radio1.on_clicked(on_view_mode)

rax2 = plt.axes([0.02, 0.64, 0.15, 0.12])
radio2 = RadioButtons(rax2, ('Lars','Scrapie','Both'))
def on_streamer(label):
    global active_streamer, mode
    active_streamer = label
    if label == 'Both':
        mode = 'Overlay'
        radio1.set_active(1)
    update_plot()
radio2.on_clicked(on_streamer)

rax3 = plt.axes([0.02, 0.50, 0.15, 0.1])
radio3 = RadioButtons(rax3, ('2','3','10','20','30','60'), active=2)
def on_duration(label):
    global duration
    duration = int(label)
    update_plot()
radio3.on_clicked(on_duration)

tax4 = plt.axes([0.02, 0.38, 0.15, 0.05])
txt_box = TextBox(tax4, 'Dur:', initial=str(duration))
def on_submit(text):
    global duration
    try:
        duration = int(text)
    except:
        pass
    update_plot()
txt_box.on_submit(on_submit)

update_plot()
plt.show()
