# Liquid metaobject loop limit repro

A small, read-only probe that shows how many entries a Liquid `for` loop reaches when it loops over a Shopify metaobject definition's `values`: in a plain loop, inside `{% paginate ... by 250 %}`, and next to a split array and a numeric range of 1,300 items. It runs against a merchant-owned definition in a normal theme section and against an app-owned definition in a theme app extension block.

It accompanies the article [Shopify Liquid Metaobject Lists Stop at 50: paginate and Array Tests](https://ilogr.com/shopify-liquid-metaobject-loop-limit-50-paginate/).

> **Use at your own risk.** This code creates and deletes test data and a theme copy on a Shopify store. Run it only on a development store you can throw away, never on a live store and never on a live theme. It is provided as is, without warranty of any kind. Nobody who wrote, published or contributed to it accepts any responsibility or liability for loss, damage, cost or anything else that results from using it. Read every script before you run it. See [LICENSE](LICENSE).

## What is in this repo

| Path | Purpose |
| --- | --- |
| `theme-overlay/sections/loop-probe.liquid` | The probe for a merchant-owned definition (a theme section). |
| `theme-overlay/sections/app-host.liquid` | A host section so the app block can be placed on a page. |
| `theme-overlay/templates/index.json` | Home page template: two probe sections (page size 250). |
| `theme-overlay/templates/search.json` | Search page template: two probes with page sizes 251 and 1000 (extra check). |
| `app/` | Theme app extension (`loop-probe` block) and an example app configuration with one app-owned definition. |
| `scripts/seed.py` | Creates the definition (merchant-owned) and tops entries up to a target count. Safe to run again. |
| `scripts/run_steps.py` | Seeds 49, 50, 51, 249, 250 and 251 entries in turn and reads the probe after each step. |
| `scripts/read_probe.py` | Reads the probe lines from a storefront, with an optional `?page=N` and keyed page-parameter check. |
| `scripts/make-theme.sh` | Copies a theme, adds the probe and pushes it as a new unpublished theme. |
| `scripts/cleanup.py` | Deletes the test definition (merchant-owned) or its entries (app-owned). |
| `scripts/run-all.sh` | One full pass of both probes. |
| `results/` | Raw outputs of the runs described below. |

## Requirements

- A Shopify development store you may delete, with its storefront password (Online Store, Preferences).
- Shopify CLI 4.9 or newer, signed in to the partner organisation that owns the store.
- Python 3.9 or newer (standard library only).
- For the app-owned part: a Shopify app you create yourself in the same organisation (steps below).

## Steps: merchant-owned definition

1. Authenticate the CLI for store commands (a browser page asks you to approve the CLI connector app with metaobject write access):
   ```bash
   shopify store auth -s YOUR-STORE.myshopify.com --scopes write_metaobject_definitions,write_metaobjects
   ```
2. Pick any existing theme as the base, note its ID (`shopify theme list -s YOUR-STORE.myshopify.com`) and make an unpublished copy with the probe added. The live theme is not touched:
   ```bash
   ./scripts/make-theme.sh YOUR-STORE.myshopify.com BASE_THEME_ID loop-limit-repro
   ```
   Note the new theme's ID from `shopify theme list`.
3. Seed and read, step by step (about two minutes per step, because the storefront reports a new count with a delay):
   ```bash
   export STORE_PASSWORD='your dev store storefront password'
   python3 scripts/run_steps.py YOUR-STORE.myshopify.com NEW_THEME_ID repro_item results/my-merchant-run.txt
   ```
   Each step waits until `values_count` equals the number seeded, then writes the probe lines. At 250 and 251 entries it also requests `?page=1`, `?page=2`, `?page=3` and the same numbers on the keyed page parameter that Shopify reports in `paginate.page_param`.
4. For a single reading at any time:
   ```bash
   python3 scripts/read_probe.py YOUR-STORE.myshopify.com NEW_THEME_ID --pages
   ```
5. Optional extra: after step 3, read the search page, where two probes use page sizes 251 and 1000:
   ```bash
   PROBE_PATH=/search python3 scripts/read_probe.py YOUR-STORE.myshopify.com NEW_THEME_ID
   ```
6. Clean up:
   ```bash
   python3 scripts/cleanup.py YOUR-STORE.myshopify.com repro_item
   shopify theme delete -s YOUR-STORE.myshopify.com -t NEW_THEME_ID
   ```

## Steps: app-owned definition (theme app extension)

1. Create an app in your organisation's Dev Dashboard (any name), copy its client ID, then make a folder for it:
   ```bash
   mkdir my-probe-app && cp -R app/extensions my-probe-app/ && cp app/shopify.app.toml.example my-probe-app/shopify.app.toml
   ```
   Edit `my-probe-app/shopify.app.toml`: set `client_id`, and make `name` match your app.
2. Deploy and install the app on the development store:
   ```bash
   cd my-probe-app && shopify app deploy --allow-updates --no-input
   ```
   Then use the Dev Dashboard's test-install link for the app and choose your development store.
3. In the theme copy from the previous section, open the theme editor on the Cart page (`/cart`), add the `App host` section and add the app block `Loop-limit probe` to it twice. Save.
4. Seed and read, as the app (the app's `$app:repro_entry` entries can only be written by the app):
   ```bash
   export STORE_PASSWORD='your dev store storefront password'
   APP_PATH=./my-probe-app PROBE_PATH=/cart python3 scripts/run_steps.py YOUR-STORE.myshopify.com NEW_THEME_ID '$app:repro_entry' results/my-app-run.txt
   ```
5. Clean up: `APP_PATH=./my-probe-app python3 scripts/cleanup.py YOUR-STORE.myshopify.com '$app:repro_entry'`, then uninstall and delete the app and the theme copy.

## Expected output

Each probe line looks like this (block or section id and `page_param` differ on your store):

```text
PROBE type=repro_item page_size=250 values_count=51 plain_loop=50 paginated_loop=51 pages=1 current_page=1 page_param="page_xxxxxxxx" split_1300=1300 range_1300=1300
```

What we got after each step, identical for the merchant-owned definition and the app-owned definition, in both of two full passes:

| Entries seeded | `values_count` | `plain_loop` | `paginated_loop` (page size 250) | `pages` |
| ---: | ---: | ---: | ---: | ---: |
| 49 | 49 | 49 | 49 | 1 |
| 50 | 50 | 50 | 50 | 1 |
| 51 | 51 | 50 | 51 | 1 |
| 249 | 249 | 50 | 249 | 1 |
| 250 | 250 | 50 | 250 | 1 |
| 251 | 251 | 50 | 250 | 2 |

On every step `split_1300` and `range_1300` were 1300, and the two probes on the same page printed identical numbers.

Page parameters, at 250 entries (one page) and at 251 entries (two pages):

| Request | At 250 entries | At 251 entries |
| --- | --- | --- |
| `?page=1`, `?page=2`, `?page=3` | `current_page=1`, `paginated_loop=250` | `current_page=1`, `paginated_loop=250` |
| keyed parameter `=1` | `current_page=1`, 250 | `current_page=1`, 250 |
| keyed parameter `=2` | `current_page=2`, 0 | `current_page=2`, 1 |
| keyed parameter `=3` | `current_page=3`, 0 | `current_page=3`, 0 |

The page parameter on these stores was a keyed name (`page_` followed by eight characters), not `page`. A plain `?page=N` is ignored; the keyed name is what moves `paginate.current_page`. Read it from `paginate.page_param`, or use `paginate.next.url`.

Extra, merchant-owned definition at 251 entries on the search page: page size 251 reached 251 entries on one page, and page size 1000 also reached 251 on one page (`pages=1` in both), so the page size was not capped at 250 for metaobject `values` in this test.

## Tested with

| Item | Value |
| --- | --- |
| Shopify CLI | 4.9.4 |
| Admin API version | 2026-10 |
| Store type | Development store, plan "Basic App Development" |
| Theme | Horizon 4.3.0 (copy, unpublished) |
| Theme app extension API version | 2026-10 |
| Feature preview store | A second development store created with the Liquid July 2026 feature preview, Horizon 4.4.0: same numbers as above in both passes (merchant-owned definition only) |

## What was and was not tested

Tested: a plain loop over `values`, a loop inside `paginate ... by 250`, a loop over a split string of 1,300 items and over the range `(1..1300)`, two paginated probes on one page, `?page=N` and the keyed page parameter, page sizes 251 and 1000 on one store, a merchant-owned definition in a theme section, an app-owned definition in a theme app extension block, and a development store with the Liquid July 2026 feature preview.

Not tested: draft entries, definitions with several fields or references, loops over other paginated lists (collection products, search results), `limit` and `offset`, more than 1,000 entries, the entries on page 2 (only how many a loop reaches there), other themes, a store with a live storefront, other API versions, and the timing of the delay before a new count is reported.

The count the storefront reports lags behind the Admin API for a while after seeding (up to about two minutes in these runs), so the scripts wait for it before reading.

## Licence

MIT, see [LICENSE](LICENSE). The licence disclaims all warranty and all liability.
