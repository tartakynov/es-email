#! /usr/bin/env python

import hashlib
import json
import os.path
import tarfile
from email.parser import Parser
from email.utils import parsedate_to_datetime
from io import StringIO

import requests

ALLOWED_HEADERS = {"message-id", "date", "file_name", "from", "to", "cc", "bcc", "x-from", "x-to", "x-cc", "x-bcc",
                   "x-folder", "x-filename", "subject"}

COMMA_SEPARATED_HEADERS = {"from", "to", "cc", "bcc", "x-from", "x-to", "x-cc", "x-bcc"}

SIGNATURE_PART_HEADERS = {"date", "subject", "from", "to"}

OUTPUT_SIZE_THRESHOLD = 67108864  # 64 MiB

TAR_FILE = "data/enron_mail_20110402.tgz"  # dataset file location

PROGRESS_FILE = "data/progress.json"  # cursor file location for saving the progress


def parse_file(parser, file_path, content):
    json_doc = {}
    msg = parser.parsestr(content)
    signature = ""
    for header, value in msg.items():
        header = header.lower()
        if header not in ALLOWED_HEADERS or not value:
            continue
        if header in SIGNATURE_PART_HEADERS:
            signature = hashlib.md5(f"{signature}:{value}".encode("utf-8")).hexdigest()
        if header in COMMA_SEPARATED_HEADERS:
            value = [v.strip() for v in value.split(",")]
        if header == "date" and "date" not in json_doc:
            value = int(parsedate_to_datetime(value).timestamp())
        json_doc[header] = value

    signature = hashlib.md5(f"{signature}:{msg.get_payload()}".encode("utf-8")).hexdigest()
    json_doc["body"] = msg.get_payload()
    json_doc["original_file_path"] = file_path
    return signature, json_doc


def bulk_upload(fp):
    print(f"uploading")
    r = requests.post('http://localhost:9200/_bulk', data=fp, headers={"Content-Type": "application/json"})
    r.raise_for_status()
    print(f"uploaded, status {r.status_code}")


def save_progress(file_path, index):
    progress = {
        "path": file_path,
        "index": index
    }

    print(f"current position: {file_path}, index {index}")
    with open(PROGRESS_FILE, "w") as fp:
        json.dump(progress, fp, indent=2)


def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return None, -1
    with open(PROGRESS_FILE, "r") as fp:
        progress = json.load(fp)
        return progress["path"], progress["index"]


def load_data():
    parser = Parser()
    tar = tarfile.open(TAR_FILE, "r:gz")

    for member in tar:
        if not member.isfile():
            continue

        with tar.extractfile(member) as eml_file:
            content = eml_file.read()

        yield parse_file(parser, member.path, content.decode("latin1"))


def main():
    eml_count = 0
    last_path, last_index = load_progress()

    out = StringIO()
    try:
        if last_index > 0:
            print(f"fast-forwarding to position {last_index}")
        for signature, json_doc in load_data():
            eml_count += 1
            if eml_count <= last_index:
                if eml_count == last_index:
                    print(f"fast-forwarding completed")
                continue

            out.write(f'{{"index":{{"_index":"enron","_id":"{signature}"}}}}\n')
            out.write(json.dumps(json_doc, separators=(',', ':')))
            out.write("\n")

            if out.tell() >= OUTPUT_SIZE_THRESHOLD:
                out.seek(0)
                bulk_upload(out)

                out.close()
                out = StringIO()
                save_progress(json_doc["original_file_path"], eml_count)
    finally:
        out.close()


if __name__ == '__main__':
    main()
