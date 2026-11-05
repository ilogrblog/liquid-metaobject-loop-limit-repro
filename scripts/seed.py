#!/usr/bin/env python3
"""Create (or top up) a test metaobject definition and entries on a development store.

Usage: seed.py <store>.myshopify.com <type> <target-count>
Example: seed.py my-dev-store.myshopify.com repro_item 51
App-owned type: APP_PATH=<app folder> seed.py <store>.myshopify.com '$app:repro_entry' 51

Idempotent: it lists the handles that already exist and creates only the missing
ones (item-0001 ... item-NNNN). It never deletes anything; see cleanup.py.
Uses the Shopify CLI (`shopify store execute`) with the API version pinned below.
"""
import json, os, subprocess, sys, tempfile, time

API_VERSION = os.environ.get("API_VERSION", "2026-10")
BATCH = 25

def run(store, query, mutate=False):
    with tempfile.NamedTemporaryFile("w", suffix=".graphql", delete=False) as f:
        f.write(query)
        path = f.name
    outpath = path + ".json"
    app_path = os.environ.get("APP_PATH")  # set for app-owned types: runs as the installed app
    if app_path:
        cmd = ["shopify", "app", "execute", "--path", app_path, "-s", store, "--version", API_VERSION,
               "--query-file", path, "--output-file", outpath]
    else:
        cmd = ["shopify", "store", "execute", "-s", store, "--version", API_VERSION,
               "--query-file", path, "--output-file", outpath, "--json"]
        if mutate:
            cmd.append("--allow-mutations")
    for attempt in range(4):  # the Admin API occasionally answers 502; retry a few times
        p = subprocess.run(cmd, capture_output=True, text=True)
        if not p.returncode and os.path.exists(outpath):
            break
        time.sleep(5 * (attempt + 1))
    os.unlink(path)
    if p.returncode or not os.path.exists(outpath):
        sys.exit("shopify store execute failed:\n" + p.stdout[-800:] + p.stderr[-800:])
    with open(outpath) as f:
        data = json.load(f)
    os.unlink(outpath)
    return data

def existing_handles(store, mtype):
    handles, after = set(), None
    while True:
        a = ', after: "%s"' % after if after else ""
        d = run(store, '{ metaobjects(type: "%s", first: 250%s) { nodes { handle } pageInfo { hasNextPage endCursor } } }' % (mtype, a))
        m = d["metaobjects"]
        handles |= {n["handle"] for n in m["nodes"]}
        if not m["pageInfo"]["hasNextPage"]:
            return handles
        after = m["pageInfo"]["endCursor"]

def ensure_definition(store, mtype):
    if os.environ.get("APP_PATH"):
        return  # app-owned definitions are declared in shopify.app.toml and released with the app
    d = run(store, '{ metaobjectDefinitionByType(type: "%s") { id } }' % mtype)
    if d["metaobjectDefinitionByType"]:
        return
    q = ('mutation { d: metaobjectDefinitionCreate(definition: {type: "%s", name: "Loop limit repro item", '
         'access: {storefront: PUBLIC_READ}, fieldDefinitions: [{key: "title", name: "Title", '
         'type: "single_line_text_field"}]}) { metaobjectDefinition { id } userErrors { message code } } }' % mtype)
    for _ in range(20):  # a just-deleted definition keeps its key reserved for a short while
        r = run(store, q, True)["d"]
        if not r["userErrors"]:
            break
        if "already in use" not in r["userErrors"][0]["message"]:
            sys.exit("definition error: %s" % r["userErrors"])
        time.sleep(15)
    else:
        sys.exit("definition error: %s" % r["userErrors"])
    print("created definition", mtype)

def main():
    store, mtype, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
    ensure_definition(store, mtype)
    have = existing_handles(store, mtype)
    missing = [i for i in range(1, target + 1) if "item-%04d" % i not in have]
    for s in range(0, len(missing), BATCH):
        parts = ['m%d: metaobjectCreate(metaobject: {type: "%s", handle: "item-%04d", fields: [{key: "title", value: "Item %04d"}]}) '
                 '{ metaobject { id } userErrors { message code } }' % (i, mtype, i, i) for i in missing[s:s + BATCH]]
        res = run(store, "mutation {\n" + "\n".join(parts) + "\n}", True)
        errs = [v["userErrors"] for v in res.values() if v and v.get("userErrors")]
        if errs:
            sys.exit("entry error: %s" % errs[0])
    print("%s: %d entries present (created %d)" % (mtype, target if len(have) <= target else len(have), len(missing)))

if __name__ == "__main__":
    main()
