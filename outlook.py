#! /usr/bin/env python

import base64
import hashlib
import json
import os
import tarfile
from email.parser import Parser
from email.utils import parsedate_to_datetime
from io import StringIO

import requests
from html2text import html2text

from decoder import decode_mime_header, decode_imap4_utf7

ALLOWED_HEADERS = {"message-id", "date", "file_name", "from", "to", "cc", "bcc", "x-from", "x-to", "x-cc", "x-bcc",
                   "x-folder", "x-filename", "subject"}

COMMA_SEPARATED_HEADERS = {"from", "to", "cc", "bcc", "x-from", "x-to", "x-cc", "x-bcc"}

TAR_FILE = "data/out.tgz"  # dataset file location

ATTACHMENTS_FOLDER = "data/attachments"

OUTPUT_SIZE_THRESHOLD = 67108864  # 64 MiB

ES_INDEX_NAME = "outlook"


def parse_body(msg):
    content_type = msg.get_content_type()
    charset = msg.get_content_charset()
    text = msg.get_payload()
    if charset != "latin1":
        text = text.encode("latin1").decode(charset)
    if content_type == "text/html":
        if text.startswith("+ADw-"):
            text = decode_imap4_utf7(text)
        text = html2text(text, bodywidth=0).strip()
        return text
    elif content_type == "text/plain":
        return text
    raise "Unknown body type: " + content_type


def _extract_file_name(params):
    result = None
    if not params:
        return result
    for key, value in params:
        if key.lower() == "filename":
            if isinstance(value, tuple):
                charset, _, value = value
                return value.encode("latin1").decode(charset)
            else:
                result = value
    return result


def get_filename(msg):
    filename = _extract_file_name(msg.get_params(None, 'content-disposition'))
    if not filename:
        filename = _extract_file_name(msg.get_params(None, 'content-type'))
    return filename


def extract_attachment(message_id_hash, msg):
    file_name = get_filename(msg)
    if not file_name:
        return None
    folder = f"{ATTACHMENTS_FOLDER}/{message_id_hash}"
    path = os.path.join(folder, file_name)
    if not os.path.exists(path):
        os.makedirs(folder, exist_ok=True)
        with open(path, "wb") as fout:
            payload = msg.get_payload()
            fout.write(base64.b64decode(payload))
    return path


def parse_file(parser, file_path, content):
    json_doc = {}
    msg = parser.parsestr(content)
    for header, value in msg.items():
        header = header.lower()
        value = value.replace("\n ", "")
        if header not in ALLOWED_HEADERS or not value:
            continue
        if header in COMMA_SEPARATED_HEADERS:
            value = [decode_mime_header(v.strip()) for v in value.split(",")]
        else:
            value = decode_mime_header(value.strip())
        if header == "date" and "date" not in json_doc:
            value = int(parsedate_to_datetime(value).timestamp())
        json_doc[header] = value
    message_id_hash = hashlib.md5(json_doc["message-id"].encode("latin1")).hexdigest()
    payload = msg.get_payload()
    json_doc["body"] = parse_body(payload[0])
    attachments = [extract_attachment(message_id_hash, a) for a in payload[1:] if a]
    if attachments:
        json_doc["attachments"] = attachments
    json_doc["original_file_path"] = file_path
    return message_id_hash, json_doc


def load_data():
    parser = Parser()
    tar = tarfile.open(TAR_FILE, "r:gz")

    for member in tar:
        if not member.isfile():
            continue

        with tar.extractfile(member) as eml_file:
            content = eml_file.read()

        yield parse_file(parser, member.path, content.decode("latin1"))


def bulk_upload(fp):
    print(f"uploading")
    r = requests.post('http://localhost:9200/_bulk', data=fp, headers={"Content-Type": "application/json"})
    r.raise_for_status()
    print(f"uploaded, status {r.status_code}")


def main():
    out = StringIO()
    try:
        for message_id_hash, json_doc in load_data():
            out.write(f'{{"index":{{"_index":"{ES_INDEX_NAME}","_id":"{message_id_hash}"}}}}\n')
            out.write(json.dumps(json_doc, separators=(',', ':')))
            out.write("\n")

            if out.tell() >= OUTPUT_SIZE_THRESHOLD:
                out.seek(0)
                bulk_upload(out)

                out.close()
                out = StringIO()
    finally:
        out.seek(0)
        bulk_upload(out)
        out.close()


if __name__ == '__main__':
    main()
