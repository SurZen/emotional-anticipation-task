import csv
from collections import Counter
p='manifests/image_catalog.csv'
ct=Counter()
with open(p,encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
        ct[row['category']]+=1
for k,v in ct.most_common():
    print(f"{k}: {v}")
