# csvtail

Last-N rows of a CSV/TSV in **constant memory**, regardless of file size.
Hand-rolled RFC-4180 state machine — handles quoted fields, embedded
newlines, doubled-quote escapes, CRLF endings. Zero deps.

```python
from csvtail import tail

# Last 100 rows of a 50 GB CSV in constant memory
last_100 = tail("huge.csv", n=100)

# Same, with the header preserved as rows[0]
last_100_with_header = tail("huge.csv", n=100, has_header=True)

# TSV
tail("logs.tsv", 50, delim="\t")
```

MIT.
