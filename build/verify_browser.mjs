/* Render every page of both sites in headless Chromium, against the same
   Content-Security-Policy and response headers Netlify will send, and report
   anything a browser objects to.

   Checked per page, per viewport, in light and dark:
     - console errors and warnings, which is how a CSP violation surfaces
     - any request that failed or answered 400+
     - horizontal overflow of the document
     - interactive controls smaller than a comfortable tap target
     - the same again with the browser's default font size raised to 24px,
       which is how a reader with large text set sees the page

   Usage: node build/verify_browser.mjs <name>=<origin> [...]           */

import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";

const targets = process.argv.slice(2).map((a) => {
  const [name, ...rest] = a.split("=");
  return { name, origin: rest.join("=") };
});
if (!targets.length) {
  console.error("usage: node build/verify_browser.mjs idlery=http://127.0.0.1:8801 ...");
  process.exit(2);
}

const PAGES = {
  idlery: ["/", "/does-not-exist"],
  corecredit: ["/", "/support", "/privacy", "/terms", "/does-not-exist"],
};

const VIEWPORTS = [
  { label: "320", width: 320, height: 900 },
  { label: "390-iphone", width: 390, height: 844 },
  { label: "768-ipad", width: 768, height: 1024 },
  { label: "1024-ipad-landscape", width: 1024, height: 768 },
  { label: "1440-laptop", width: 1440, height: 900 },
  { label: "1920-desktop", width: 1920, height: 1080 },
];

const SHOT_DIR = "/tmp/site-shots";
mkdirSync(SHOT_DIR, { recursive: true });

const problems = [];
const note = (where, msg) => problems.push(`${where}: ${msg}`);

// Chromium's own noise, not the page's.
const IGNORE = [/favicon\.ico/i, /Failed to load resource: the server responded with a status of 404 \(File not found\)$/];

const browser = await chromium.launch();

for (const { name, origin } of targets) {
  for (const scheme of ["light", "dark"]) {
    const context = await browser.newContext({ colorScheme: scheme });
    for (const path of PAGES[name]) {
      for (const vp of VIEWPORTS) {
        const page = await context.newPage();
        await page.setViewportSize({ width: vp.width, height: vp.height });
        const where = `${name}${path} [${vp.label} ${scheme}]`;

        page.on("console", (m) => {
          if (m.type() !== "error" && m.type() !== "warning") return;
          const text = m.text();
          if (IGNORE.some((re) => re.test(text))) return;
          // The 404 route is *meant* to answer 404; the browser logs that.
          if (path === "/does-not-exist" && /status of 404/.test(text)) return;
          note(where, `console ${m.type()}: ${text}`);
        });
        page.on("pageerror", (e) => note(where, `page error: ${e.message}`));
        page.on("requestfailed", (r) => {
          const u = r.url();
          if (IGNORE.some((re) => re.test(u))) return;
          // A cancelled request is the browser changing its mind about a
          // srcset candidate, or the page closing — not a broken asset.
          const why = r.failure()?.errorText || "";
          if (why.includes("ERR_ABORTED")) return;
          note(where, `request failed: ${u} (${why})`);
        });
        page.on("response", (r) => {
          const expected404 = path === "/does-not-exist" && r.url().endsWith("/does-not-exist");
          if (r.status() >= 400 && !expected404 && !IGNORE.some((re) => re.test(r.url()))) {
            note(where, `HTTP ${r.status()} for ${r.url()}`);
          }
        });

        await page.goto(origin + path, { waitUntil: "networkidle" });

        for (const fontSize of [16, 24]) {
          if (fontSize !== 16) {
            const cdp = await context.newCDPSession(page);
            await cdp.send("Page.setFontSizes", { fontSizes: { standard: fontSize } });
            await page.waitForTimeout(150);
          }
          const label = fontSize === 16 ? where : `${where} font=${fontSize}px`;

          const overflow = await page.evaluate(() => {
            const doc = document.documentElement;
            const over = doc.scrollWidth - doc.clientWidth;
            if (over <= 1) return null;
            const guilty = [];
            for (const el of document.querySelectorAll("body *")) {
              const r = el.getBoundingClientRect();
              if (r.width === 0) continue;
              // The skip link parks itself far off to the left until focused;
              // that costs no scroll width and is not what is overflowing.
              if (r.right < 0) continue;
              if (r.right > doc.clientWidth + 1) {
                guilty.push(
                  `${el.tagName.toLowerCase()}.${(el.className || "").toString().split(" ")[0]}` +
                    ` right=${Math.round(r.right)}`
                );
              }
            }
            return { over, guilty: guilty.slice(0, 5) };
          });
          if (overflow) {
            note(label, `horizontal overflow of ${overflow.over}px — ${overflow.guilty.join(", ")}`);
          }

          const small = await page.evaluate(() => {
            const out = [];
            for (const el of document.querySelectorAll("a[href], button")) {
              const r = el.getBoundingClientRect();
              if (r.width === 0 || r.height === 0) continue;
              // Links inside a run of prose are exempt: they are text, and the
              // tap-target minimum applies to standalone controls.
              const inProse = el.closest("p, li, dd, figcaption, .site-footer__legal");
              if (inProse) continue;
              if (r.height < 40 || r.width < 40) {
                out.push(`${el.tagName.toLowerCase()} "${(el.textContent || "").trim().slice(0, 28)}" ${Math.round(r.width)}x${Math.round(r.height)}`);
              }
            }
            return out;
          });
          for (const s of small) note(label, `tap target under 40px: ${s}`);

          if (fontSize !== 16) {
            const cdp = await context.newCDPSession(page);
            await cdp.send("Page.setFontSizes", { fontSizes: { standard: 16 } });
          }
        }

        if (["390-iphone", "768-ipad", "1440-laptop"].includes(vp.label)) {
          const slug = `${name}${path.replace(/\//g, "_")}-${vp.label}-${scheme}`;
          await page.screenshot({ path: `${SHOT_DIR}/${slug}.png`, fullPage: path === "/" });
        }
        await page.close();
      }
    }
    await context.close();
  }
}

await browser.close();

writeFileSync(`${SHOT_DIR}/report.txt`, problems.join("\n"));
if (problems.length) {
  console.log(problems.join("\n"));
  console.log(`\n${problems.length} problem(s)`);
  process.exit(1);
}
console.log("0 problems across every page, viewport, colour scheme and font size");
