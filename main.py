import argparse
import json
import zipfile
import sqlite3
import os
from datetime import datetime

parser = argparse.ArgumentParser()

def unzip(input_path: str, output_path: str):
    with zipfile.ZipFile(input_path, 'r') as zip_ref:
        zip_ref.extractall(output_path)

def determine_collection_path(output_path: str) -> str:
    anki2_path = ""
    for file in os.listdir(output_path):
        if file.endswith(".anki21"):
            return os.path.join(output_path, file)
        elif file.endswith("anki2"):
            anki2_path = os.path.join(output_path, file)
    return anki2_path

def get_collection_connection(path: str):
    try:
        return sqlite3.connect(path)
    except Exception as e:
        print(e)

def parse_log(conn, user_id, output_path):
    cur = conn.cursor()
    cur.execute("SELECT revlog.id, cid, ease, did, revlog.ivl, revlog.factor, lapses FROM revlog LEFT JOIN cards on revlog.cid = cards.id")

    rows = cur.fetchall()

    history = []
    for row in rows:
        timestamp_id = row[0]
        record_id = user_id + str(timestamp_id)
        date = datetime.fromtimestamp(timestamp_id / 1000.0).isoformat()
        fact_id = row[1]
        response_ease = row[2] # extra data, ease
        response = response_ease != 1
        deck_id = row[3]
        srs_interval = row[4]
        ease_factor = row[5]
        lapses = row[6] # when a fact previously answered correctly is answered incorrectly
        history.append({
            "record_id": record_id,
            "user_id": user_id,
            "fact_id": fact_id,
            "deck_id": deck_id,
            "response": response,
            "date": date,
            "srs_interval": srs_interval,
            "ease_factor": ease_factor,
            "lapses": lapses
        })
    with open(output_path + 'karl_compatible_log.json', 'w') as outfile:
        json.dump(history, outfile)

if __name__ == '__main__':
    parser.add_argument('--input_path',
                        type=str,
                        help='pass path for input colpkg or apkg file')
    parser.add_argument('--output_path',
                        type=str,
                        help='pass path for output folder')
    parser.add_argument('--user_id',
                        type=str,
                        default="testuser",
                        help='pass user id')
    args = parser.parse_args()
    input_path = args.input_path
    output_path = args.output_path
    user_id = args.user_id
    unzip(input_path, output_path)
    collection_path = determine_collection_path(output_path)

    collection_connection = get_collection_connection(collection_path)
    parse_log(collection_connection, user_id, output_path)
# Accepts colpkg and apkg, check if there is collection.anki21 and if it exists, look through revlog
# collection.anki2 if there is no collection.anki21

