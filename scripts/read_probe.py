#!/usr/bin/env python3
"""Read the probe output from a password-protected development storefront.

Usage: STORE_PASSWORD=... [PROBE_PATH=/cart] read_probe.py <store>.myshopify.com <theme-id> [--pages]
Prints the PROBE lines for the plain URL. With --pages it also requests ?page=N and the
keyed page parameter (paginate.page_param) for N = 1, 2, 3.
The password is the dev store's storefront password (Online Store > Preferences).
"""
import http.cookiejar, os, re, sys, tempfile, time, urllib.error, urllib.parse, urllib.request

store, theme = sys.argv[1], sys.argv[2]
base = "https://" + store
PAGE = os.environ.get("PROBE_PATH", "/")  # "/" for the merchant probe, "/cart" for the app-extension probe
JAR = os.path.join(tempfile.gettempdir(), "loop-limit-repro-%s.cookies" % store)
jar = http.cookiejar.MozillaCookieJar(JAR)
if os.path.exists(JAR):
    jar.load(ignore_discard=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def get(path):
    for attempt in range(6):  # back off when the storefront answers 429 Too Many Requests
        try:
            return op.open(base + path).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 502, 503):
                raise
            time.sleep(10 * (attempt + 1))
    raise SystemExit("storefront kept answering an error status")

def unlock():
    html = get("/password")
    tok = re.search(r'name="authenticity_token" value="([^"]+)"', html)
    data = {"form_type": "storefront_password", "utf8": "✓", "password": os.environ["STORE_PASSWORD"]}
    if tok:
        data["authenticity_token"] = tok.group(1)
    op.open(base + "/password", urllib.parse.urlencode(data).encode())
    jar.save(ignore_discard=True)

def probe(qs=""):
    sep = "&" if "?" in qs else "?"
    html = get(PAGE + qs + sep + "preview_theme_id=" + theme)
    return re.findall(r"PROBE [^<]*", html)

lines = probe()
if not lines:  # not unlocked yet (the cookie is cached so the password form is posted only once)
    unlock()
    lines = probe()
if not lines:
    sys.exit("no PROBE line found: check the password, theme id and that the theme is the probe copy")
for l in lines:
    print(l)
if "--pages" in sys.argv:
    key = re.search(r'page_param="([^"]+)"', lines[0]).group(1)
    for n in (1, 2, 3):
        for q in ("?page=%d" % n, "?%s=%d" % (key, n)):
            print("# GET " + PAGE + q)
            for l in probe(q):
                print(l)
