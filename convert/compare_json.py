import json
import os
import argparse

def compare_json_ids(file1_path, file2_path):
    file1_path = os.path.abspath(file1_path)
    file2_path = os.path.abspath(file2_path)

    with open(file1_path, 'r', encoding='utf-8') as file1:
        data1 = json.load(file1)

    with open(file2_path, 'r', encoding='utf-8') as file2:
        data2 = json.load(file2)

    ids1 = {entry['id'] for entry in data1}
    ids2 = {entry['id'] for entry in data2}

    only_in_file1 = ids1 - ids2
    only_in_file2 = ids2 - ids1

    if only_in_file1:
        print("IDs only in File 1:")
        for id in only_in_file1:
            print(id)
    else:
        print("No unique IDs in File 1.")

    if only_in_file2:
        print("IDs only in File 2:")
        for id in only_in_file2:
            print(id)
    else:
        print("No unique IDs in File 2.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare IDs in two JSON files.")
    parser.add_argument("file1", help="Path to the first JSON file.")
    parser.add_argument("file2", help="Path to the second JSON file.")

    args = parser.parse_args()

    compare_json_ids(args.file1, args.file2)
