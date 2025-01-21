import json
import os
import sys
from datetime import datetime
from statistics import mean

def convert_time(load_times, unit):
    if unit == "sec":
        return [t / 1000 for t in load_times]
    elif unit == "min":
        return [t / (1000 * 60) for t in load_times]
    elif unit == "hours":
        return [t / (1000 * 60 * 60) for t in load_times]
    return load_times

def main():
    if len(sys.argv) < 3 or sys.argv[1] != "-d":
        print("Usage: script.py -d <unit: sec|min|hours>")
        return

    unit = sys.argv[2]
    if unit not in {"sec", "min", "hours"}:
        print("Invalid unit. Use 'sec', 'min', or 'hours'.")
        return

    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '..', 'data')
    json_path = os.path.join(data_dir, 'export.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        events = json.load(f)

    events.sort(key=lambda e: e["datetime"])

    daily_loads = {}
    prev_event = None
    for event in events:
        current_dt = datetime.fromisoformat(event["datetime"].replace("Z", "+00:00"))
        if prev_event:
            prev_dt = datetime.fromisoformat(prev_event["datetime"].replace("Z", "+00:00"))
            elapsed_ms = (current_dt - prev_dt).total_seconds() * 1000
            load_time = elapsed_ms - prev_event["timeSpent"]
            day = current_dt.date()
            daily_loads.setdefault(day, []).append(load_time)
        prev_event = event

    for day, loads in daily_loads.items():
        converted_loads = convert_time(loads, unit)
        avg_load = mean(converted_loads) if converted_loads else 0
        print(f"{day}: Average Load Time = {avg_load:.2f} {unit}")

if __name__ == "__main__":
    main()
