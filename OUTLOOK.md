The script named `outlook.py` indexes Outlook PST files to Elastic.

## Prerequisites

- Python 3
- [readpst](https://linux.die.net/man/1/readpst)
- Dependencies from the requirements.txt

## Steps

0. Install requirements

```shell
pip install -r requirements.txt
sudo apt install pst-utils # debian
```

1. Create the index in Elastic

```shell
curl -sX PUT "http://localhost:9200/outlook" \
  -H "Content-Type: application/json" \
  --data-binary @indexes/outlook.json | jq
```

3. Convert your PST file into EML files

```shell
mkdir -p out
readpst -t e -e your_pst_file.pst -o out
```

4. Create a tarball from your folder

```shell
tar -czvf out.tgz out
```

5. Upload the json manually

```shell
curl -sX POST "http://localhost:9200/_bulk" \
  -H "Content-Type: application/json" \
  --data-binary @out.json | jq
```

6. You can delete the index if you want to re-upload the data

```shell
curl -sX DELETE "http://localhost:9200/outlook" | jq
```

