import csv
import json

def csv_to_json(input_file, output_file):
    data = []

    with open(input_file, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        
        for row in csv_reader:
            entry = {
                "id": int(row["id"]),
                "mapId": int(row["mapId"]),
                "player": row["player"],
                "datetime": row["datetime"].replace(' ', 'T').split('.')[0] + 'Z',
                "medal": row["medal"],
                "timeSpent": int(row["timeSpent"]),
                "mapper": row["mapper"],
                "styles": row["styles"],
                "skipType": row["skipType"],
                "atTime": int(row["atTime"]),
                "finalTime": int(row["finalTime"]),
                "currentMedalCount": int(row["currentMedalCount"]),
                "freeSkipCount": int(row["freeSkipCount"]),
                "pbBeforeFin": int(row["pbBeforeFin"]),
                "mapTitle": row["mapTitle"],
                "currentGoldCount": int(row["currentGoldCount"])
            }
            data.append(entry)

    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

input_file = 'random_maps.csv'
output_file = 'export.json'
csv_to_json(input_file, output_file)
