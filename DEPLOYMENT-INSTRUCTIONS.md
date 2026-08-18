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

## 10. Before you launch

**Have an attorney review the Privacy Policy and Terms of Service before the app
is publicly available.** Both documents are written to describe what CoreCredit
actually does, and they carry a real effective date of 18 August 2026 rather than
a placeholder — but they have not been reviewed by counsel, and they set out
governing law (Ohio), exclusive venue (Butler County, Ohio), warranty disclaimers,
a liability cap, and indemnification. Those are the clauses worth a lawyer's hour.

Two things to decide with that review:

- **The subscription section of the Terms** describes the free tier (five
  simultaneously unresolved cores) and the Pro entitlement (unlimited), and states
  that Apple sets and displays pricing. No price is hard-coded on the website, so
  nothing needs changing there when pricing is finalised.
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

## Known follow-up for version 2

The Idlery brand artwork was not available when these sites were built, so the
Idlery wordmark currently renders as text in the brand teal, and the favicon,
touch icon and social-preview mark are simple on-brand stand-ins generated
locally — deliberately plainer than the real Idlery square mark rather than an
imitation of it. The CoreCredit app icon **is** the real artwork throughout.

When the wordmark and square-mark files are available:

1. Sample the exact brand colours from the artwork and update the six teal tokens
   at the top of `assets/css/idlery.css`.
2. Add `idlery-wordmark-light.png` and `idlery-wordmark-dark.png` to
   `assets/img/`, and replace `<span class="wordmark">idlery</span>` in the header
   and footer with the two `<img class="wordmark-img wordmark-light/dark">`
   elements. The light/dark switching rules are already in the stylesheet, and the
   markup carries a comment showing the exact replacement.
3. Regenerate the mark derivatives and the Open Graph image from the real square
   mark.

Similarly, the CoreCredit "A look at the app" section currently describes the six
screens in words and says plainly that screenshots will be published when the app
reaches the App Store. No mock-ups or invented app UI appear anywhere on either
site. When real screenshots exist, each `<li>` in that section takes an image
above its heading, and the CoreCredit card on idlery.com has a matching slot where
the at-a-glance panel now sits.
