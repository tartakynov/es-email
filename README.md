## Prerequisites
- Python 3
- Dependencies from the requirements.txt

## Steps
0. Data file `enron_mail_20110402.tgz`
1. Create an index in Elastic
```shell
curl -sX PUT "http://localhost:9200/enron" \
  -H "Content-Type: application/json" \
  --data-binary @enron-index.json | jq
```
2. Prepare Elastic [Bulk API](https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html) JSON files
3. Upload the files via the bulk upload endpoint
```shell
curl -sX POST "http://localhost:9200/_bulk" \
  -H "Content-Type: application/json" \
  --data-binary @data/output.json
```
4. Delete index if needed
```shell
curl -sX DELETE "http://localhost:9200/enron" | jq
```

## Links
- http://praveendiary.blogspot.com/2014/10/elastic-search-experimentation-with.html
- https://gssachdeva.wordpress.com/2016/03/20/mining-mailboxes-with-elasticsearch-and-kibana/
- https://kb.objectrocket.com/elasticsearch/how-to-use-python-helpers-to-bulk-load-data-into-an-elasticsearch-index

