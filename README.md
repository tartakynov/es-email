The script named `enron.py` indexes the Enron mail dataset to Elastic.

## Prerequisites
- Python 3
- Dependencies from the requirements.txt

## Steps
0. Download the dataset file [enron_mail_20110402.tgz](http://www.cs.cmu.edu/~enron/enron_mail_20110402.tgz) into `data/` folder
1. Install requirements
```shell
pip install -r requirements.txt
```
2. Create the index in Elastic
```shell
curl -sX PUT "http://localhost:9200/enron" \
  -H "Content-Type: application/json" \
  --data-binary @indexes/enron.json | jq
```
3. Run the script
```shell
./enron.py
```
4. You can delete the index if you want to re-upload the data
```shell
curl -sX DELETE "http://localhost:9200/enron" | jq
```

## Links
- http://praveendiary.blogspot.com/2014/10/elastic-search-experimentation-with.html
- https://gssachdeva.wordpress.com/2016/03/20/mining-mailboxes-with-elasticsearch-and-kibana/
- https://kb.objectrocket.com/elasticsearch/how-to-use-python-helpers-to-bulk-load-data-into-an-elasticsearch-index
