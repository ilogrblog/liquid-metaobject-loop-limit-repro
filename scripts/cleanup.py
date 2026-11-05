#!/usr/bin/env python3
"""Delete a test metaobject definition and all of its entries.

Usage: cleanup.py <store>.myshopify.com <type>
Only run this against a development store and a type created by seed.py.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from seed import run, existing_handles
import time

store, mtype = sys.argv[1], sys.argv[2]
if os.environ.get("APP_PATH"):  # app-owned: delete the entries; the definition goes with the app
    r = run(store, 'mutation { x: metaobjectBulkDelete(where: {type: "%s"}) { job { id } userErrors { message } } }' % mtype, True)["x"]
    print(r)
    for _ in range(40):  # the bulk delete runs as a background job; wait until the entries are gone
        if not existing_handles(store, mtype):
            break
        time.sleep(5)
    sys.exit(0)
d = run(store, '{ metaobjectDefinitionByType(type: "%s") { id name } }' % mtype)["metaobjectDefinitionByType"]
if not d:
    sys.exit("no definition of type %s" % mtype)
r = run(store, 'mutation { x: metaobjectDefinitionDelete(id: "%s") { deletedId userErrors { message } } }' % d["id"], True)["x"]
print(r)
