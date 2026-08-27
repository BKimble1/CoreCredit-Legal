# Deployment instructions

Two independent static sites, each packaged as a drag-and-drop Netlify archive.

| Archive | Becomes | Contains |
|---|---|---|
| `idlery-netlify.zip` | `https://idlery.com` | Company homepage, 404, redirects for the alternate domains |
| `corecredit-netlify.zip` | `https://corecredit.idlery.com` | `/`, `/support`, `/privacy`, `/terms`, 404 |

Both extract with `index.html` at the archive root. Neither has a build step, a
package manager, an external font, a CDN dependency, an analytics script, or a
cookie of any kind — so there is nothing to configure beyond the domains.

---

## 1. Create the Idlery site

1. Sign in at <https://app.netlify.com> and go to **Sites**.
2. Drag **`idlery-netlify.zip`** onto the deploy drop zone ("Want to deploy a new
   site without connecting to Git? Drag and drop your site output folder here").
   Netlify unpacks the archive and publishes it at a temporary
   `random-name.netlify.app` address.
3. Open the new site, then **Site configuration → Change site name**, and give it
   something recognisable such as `idlery`.

Confirm the temporary address loads before going further.

## 2. Assign `idlery.com` as the primary domain

1. **Domain management → Add a domain** → enter `idlery.com` → **Verify** → **Add**.
2. Netlify will ask whether to use Netlify DNS or an external DNS provider.
   Pick whichever matches where the domain is registered — see step 6 for the
   records either way.
3. Once the domain is attached, open its **⋯** menu and choose
   **Set as primary domain**. `idlery.com` must be the primary, not the `www`
   form, because the shipped redirects fold everything else into the apex.

## 3. Add the alias domains

The `_redirects` file inside `idlery-netlify.zip` already contains permanent
(`301`) host redirects:

```
idleryservices.com        →  https://idlery.com
www.idleryservices.com    →  https://idlery.com
www.idlery.com            →  https://idlery.com
```

**Those rules only run for hosts Netlify actually serves.** A domain Netlify has
never heard of never reaches the redirect engine, so each one must be added as a
domain alias on this site:

1. **Domain management → Add a domain**, and add each of:
   - `www.idlery.com`
   - `idleryservices.com`
   - `www.idleryservices.com`
2. Leave `idlery.com` as the primary. The other three stay as aliases.
3. Point each alias at Netlify in DNS (step 6) and let the certificate cover
   all four names (step 7).

## 4. Create the CoreCredit site

1. Back at **Sites**, drag **`corecredit-netlify.zip`** onto the deploy drop zone.
   This must be a **second, separate Netlify site** — do not redeploy over the
   Idlery one.
2. Rename it to something like `corecredit`.

## 5. Assign `corecredit.idlery.com`

1. On the CoreCredit site: **Domain management → Add a domain** →
   `corecredit.idlery.com` → **Add**.
2. Set it as the primary domain for that site.

A subdomain of `idlery.com` can be served by a different Netlify site from the
apex; that is the normal arrangement and needs no special setting.

## 6. DNS records

Use the exact values Netlify shows you under **Domain management → DNS
configuration** for each domain. Netlify displays the current values, and they
are what you should enter — the shapes below are only so you know what to expect.

**If `idlery.com` uses Netlify DNS**, change the nameservers at your registrar to
the four `dnsN.p0X.nsone.net` hostnames Netlify lists, then let Netlify create the
records. This is the simplest option and handles the apex correctly.

**If `idlery.com` stays on external DNS**, create:

| Host | Type | Value |
|---|---|---|
| `idlery.com` (apex) | `A` (or `ALIAS`/`ANAME` if your provider offers one) | the load-balancer IP Netlify shows |
| `www.idlery.com` | `CNAME` | the Idlery site's `<name>.netlify.app` |
| `corecredit.idlery.com` | `CNAME` | the **CoreCredit** site's `<name>.netlify.app` |

For `idleryservices.com`, the same pattern on that domain's own DNS: apex `A`
(or `ALIAS`) to Netlify, `www` as a `CNAME` to the **Idlery** site.

> Point `corecredit.idlery.com` at the CoreCredit site, not the Idlery one. A
> subdomain aimed at the wrong site is the single most common mistake here, and
> it presents as the company homepage appearing at the product address.

DNS changes can take anywhere from a few minutes to a few hours to propagate.

## 7. Enable HTTPS

1. On each site: **Domain management → HTTPS**.
2. Wait until DNS resolves, then choose **Verify DNS configuration** and
   **Provision certificate**. Netlify issues a free Let's Encrypt certificate.
3. On the Idlery site, make sure the certificate covers all four names
   (`idlery.com`, `www.idlery.com`, `idleryservices.com`,
   `www.idleryservices.com`). Re-provision after adding an alias if one is
   missing — a redirect from a domain with no certificate fails before it can
   redirect.
4. Turn **Force HTTPS** on for both sites.

The sites also send `Strict-Transport-Security` from their `_headers` file, so
browsers will remember to use HTTPS after the first visit.

## 8. Verify after deploying

Open each of these directly in a browser — typed into the address bar, not
reached by clicking through — and confirm a `200` and the right page:

- `https://idlery.com/`
- `https://idlery.com/404-check` → the branded Idlery 404 page
- `https://corecredit.idlery.com/`
- `https://corecredit.idlery.com/support`
- `https://corecredit.idlery.com/privacy`
- `https://corecredit.idlery.com/terms`
- `https://corecredit.idlery.com/404-check` → the branded CoreCredit 404 page

Then confirm each redirect lands on `https://idlery.com/`:

- `http://idleryservices.com`
- `https://www.idleryservices.com`
- `https://www.idlery.com`

The three CoreCredit legal URLs are the ones App Review opens, so check them
last and check them directly. If any returns a 404, the usual cause is a deploy
that unpacked the archive into a subfolder — re-drag the ZIP rather than a folder
containing it.

## 9. Update the CoreCredit app configuration

Once the URLs resolve, replace the placeholder values in the app. They are all in
one file, `CoreCredit/App/AppConfiguration.swift`:

| Setting | New value |
|---|---|
| Marketing URL | `https://corecredit.idlery.com` |
| Support URL | `https://corecredit.idlery.com/support` |
| Privacy URL | `https://corecredit.idlery.com/privacy` |
| Terms URL | `https://corecredit.idlery.com/terms` |
| Support email | `support@idlery.com` |

The same four URLs go into App Store Connect — Privacy Policy URL is mandatory,
and an auto-renewable subscription also requires a Terms of Use (EULA) link.
Use the marketing URL for the app's Marketing URL field.

## 10. After a launch update

The archives now carry the launched product. Re-drag them onto the two existing
Netlify sites (**Deploys → drag and drop**), then check the launch-specific
things directly in a browser:

- `https://corecredit.idlery.com/` shows **Available now on the App Store**, a
  **Download on the App Store** button, and real app screenshots.
- Every App Store button on both sites lands on
  <https://apps.apple.com/app/corecredit-core-return-ledger/id6802336957>.
- On an iPhone, `corecredit.idlery.com` shows Safari's Smart App Banner for
  CoreCredit at the top of the page, and the download button opens the App Store
  app rather than a web page.
- On a desktop, the QR code at the foot of the CoreCredit page scans to the same
  listing. (`build/make_qr.py` regenerates it and proves it decodes by
  rasterising the written SVG and reading it back.)
- `https://idlery.com/` says CoreCredit is available, with no "coming soon"
  anywhere — `build/check_content.py` fails the build if that language returns.

## 11. The legal pages still want a lawyer's hour

**The Privacy Policy and Terms of Service have not been reviewed by counsel.**
The app is now publicly available, so this is no longer a pre-launch item — it is
an outstanding one. Both documents describe what CoreCredit actually does and
carry a real effective date of 18 August 2026 rather than a stand-in, but they set
out governing law (Ohio), exclusive venue (Butler County, Ohio), warranty
disclaimers, a liability cap, and indemnification. Those are the clauses worth an
attorney's time.

Neither document's promises were changed by the launch update; only the pages'
launch-state wording was. Two things to raise at that review:

- **The subscription section of the Terms** describes the free tier (five
  simultaneously unresolved cores) and the Pro entitlement (unlimited), and states
  that Apple sets and displays pricing. **No price appears anywhere on either
  website** — deliberately, so a storefront price change can never make the site
  wrong. Apple shows the current price on the listing and on the paywall.
- **Apple's terms.** The Terms state that Apple's Media Services terms and standard
  EULA apply *alongside* them. If you later configure a custom EULA in App Store
  Connect, revisit that section.

Nothing on either live site says "draft", "placeholder", or "not legal advice" —
that note belongs here, not on the public pages.

---

## What is in each archive

```
idlery-netlify.zip                 corecredit-netlify.zip
├── index.html                     ├── index.html
├── 404.html                       ├── support/index.html
├── robots.txt                     ├── privacy/index.html
├── sitemap.xml                    ├── terms/index.html
├── _headers                       ├── 404.html
├── _redirects                     ├── robots.txt
└── assets/                        ├── sitemap.xml
    ├── css/idlery.css             ├── _headers
    ├── js/nav.js                  ├── _redirects
    └── img/                       └── assets/
                                       ├── css/corecredit.css
                                       └── img/
```

`_headers` sets a restrictive Content-Security-Policy (`default-src 'none'` with
`'self'` only for images, styles and scripts), `X-Content-Type-Options`,
`X-Frame-Options`, `Referrer-Policy`, a `Permissions-Policy` that denies camera,
microphone, geolocation and payment, HSTS, and long-lived immutable caching for
`/assets/*`. Netlify reads both `_headers` and `_redirects` from the deploy root;
they are not served as pages.

`assets/js/nav.js` on the Idlery site is the only JavaScript on either site. It
highlights the nav link for the section in view and does nothing else — every
page is complete and navigable with JavaScript disabled.

## Updating a site later

Re-drag the new ZIP onto the same Netlify site's **Deploys** tab. Domains, DNS,
and certificates stay attached to the site, so they survive a redeploy. Keep the
two sites separate; deploying one archive over the other's site will replace it.

## Regenerating the assets

Both sites' images are generated from artwork that lives in other repositories,
by scripts in `build/`. Nothing is drawn by hand and nothing is invented.

| Command | What it produces |
|---|---|
| `python3 build/make_brand_assets.py <IdleryWordmark.png>` | The Idlery wordmark (light and dark, transparent), the square mark, the favicon and touch icon, and `idlery-og.png`. Every glyph shape comes out of the supplied artwork's own alpha channel; the brand teal `#3aa6ab` is sampled from it. |
| `python3 build/make_screenshots.py <CoreCredit repo> <corecredit-appstore repo>` | The device captures used on both sites. Each is cropped to remove the iOS status bar and re-encoded; no app UI is redrawn, recoloured or composited. |
| `python3 build/make_og.py` | `corecredit-og.png`, the CoreCredit social card. |
| `python3 build/make_qr.py` | `appstore-qr.svg`, and it fails unless the written file rasterises and decodes back to the exact App Store URL. |
| `python3 build/prune_assets.py` | Deletes any image no page references. |

`build/make_idlery_assets.py`, which drew interim stand-in brand artwork while
the real wordmark was unavailable, has been removed: the real artwork is in use
and re-running that script would have replaced it with the stand-ins.

## Checking a change before you deploy

`bash build/verify.sh` serves both sites locally **with their own `_headers`
applied** and runs everything:

| Check | What it catches |
|---|---|
| `build/check.py` | Malformed HTML, heading jumps, duplicate ids, images without `alt` or dimensions, and any local link or image reference that does not resolve. |
| `build/contrast.py` | Every foreground/background pair the sites use, in light and dark, against WCAG AA. The palettes are parsed out of the stylesheets, so a token change is checked at its new value. |
| `build/check_content.py` | Stale launch language, a wrong App Store URL or ID, invalid JSON-LD, a missing canonical or social card, a Smart App Banner in the wrong place, an unexpected outbound host, `_redirects` and `sitemap.xml` entries that point nowhere. |
| `build/verify_browser.mjs` | Renders every page in headless Chromium at 320 / 390 / 768 / 1024 / 1440 / 1920, in light and dark, at the default font size and at 24px, and reports console errors (which is how a CSP violation shows up), failed requests, horizontal overflow, and tap targets under 40px. |

The local server applying the real `Content-Security-Policy` is the point of it:
`style-src 'self'` silently drops an inline `style` attribute, and a browser
reports that only as a console violation. That is how the inline styles that had
been on these pages since they were written were found and removed.
