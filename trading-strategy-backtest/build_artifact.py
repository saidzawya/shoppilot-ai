#!/usr/bin/env python3
"""Assemble the self-contained HTML research artifact (charts inlined as
data URIs). Keeps the giant base64 out of the assistant's context."""
import base64, json

def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()

charts = b64("out/report_charts.png")
mc = b64("out/montecarlo_bootstrap.png")
a = json.load(open("out/analysis.json"))
b = a["base_core"]

HTML = f"""<main>
<header class="hero">
  <div class="eyebrow">Quantitative falsification study · GC=F gold · 39 trading days · N=36</div>
  <h1>The US-open box-breakout strategy does <span class="kill">not</span> demonstrate a reliable edge.</h1>
  <p class="lede">Tested on the largest dataset obtainable, the strategy is statistically
  indistinguishable from no edge. Its entire profit rests on one trade in thirty-six, its
  out-of-sample first half loses money, and its expectancy turns negative under realistic
  trading costs. A real edge may exist below the noise floor — but 39 days cannot show it.</p>
  <div class="verdict-row">
    <div class="v v-fail"><span class="dot"></span>Statistically robust edge</div>
    <div class="v v-fail"><span class="dot"></span>Shows promise, needs validation</div>
    <div class="v v-on"><span class="dot"></span>No reliable edge demonstrated</div>
  </div>
</header>

<section class="stats">
  <div class="stat"><div class="k">Win rate</div><div class="val">36%</div><div class="s">13W / 23L</div></div>
  <div class="stat"><div class="k">Profit factor</div><div class="val">1.23</div><div class="s">floor ≈ 1.3–1.5</div></div>
  <div class="stat"><div class="k">Expectancy</div><div class="val">+0.14<span class="u">R</span></div><div class="s">95% CI [−0.41, +0.78]</div></div>
  <div class="stat flag"><div class="k">P(expectancy ≤ 0)</div><div class="val">0.33</div><div class="s">need &lt; 0.05 · <b>cannot reject H₀</b></div></div>
  <div class="stat"><div class="k">Median trade</div><div class="val">−1.0<span class="u">R</span></div><div class="s">typical trade is a full loss</div></div>
  <div class="stat flag"><div class="k">Drop best trade</div><div class="val">−0.01<span class="u">R</span></div><div class="s">edge flips negative</div></div>
</section>

<section class="block">
  <h2>The four falsification tests — all failed</h2>
  <div class="tests">
    <div class="test fail"><h3>1 · Significance</h3><p>Bootstrap <b>P(expectancy≤0)=0.33</b>. The 95% CI on expectancy
      spans a losing system to a good one. 36 trades cannot resolve it; ~250–400 are needed.</p></div>
    <div class="test fail"><h3>2 · Outlier independence</h3><p>Removing the single best trade (of 36) drops
      expectancy from <b>+0.144R to −0.012R</b>. Remove two → −0.14R. The profit is a lottery ticket.</p></div>
    <div class="test fail"><h3>3 · Out-of-sample</h3><p>First half (May 13–Jun 9): <b>−2.18R, PF 0.82 — losing.</b>
      All profit sits in the back half. Window-1 also negative. Period-dependent, not edge.</p></div>
    <div class="test fail"><h3>4 · Realistic execution</h3><p>Expectancy hits zero at <b>$0.30/side</b> cost and
      goes <b>negative at $0.50</b>. Retail gold cost is $0.30–0.60/side. The paper edge dies at the broker.</p></div>
  </div>
</section>

<section class="block">
  <h2>Evidence</h2>
  <img class="chart" alt="Equity curve, drawdown, R-distribution, monthly P&L, walk-forward and outlier sensitivity"
       src="data:image/png;base64,{charts}"/>
  <img class="chart" alt="Monte Carlo equity distribution and bootstrap of expectancy"
       src="data:image/png;base64,{mc}"/>
</section>

<section class="block">
  <h2>Execution-cost decay</h2>
  <div class="tablewrap"><table>
    <thead><tr><th>Cost / side</th><th>Total R</th><th>Expectancy</th><th>Profit factor</th></tr></thead>
    <tbody>
      <tr><td>$0.00 (ideal)</td><td>+5.19</td><td>+0.144</td><td>1.23</td></tr>
      <tr><td>$0.15</td><td>+3.39</td><td>+0.094</td><td>1.14</td></tr>
      <tr class="warn"><td>$0.30</td><td>+1.61</td><td>+0.045</td><td>1.06</td></tr>
      <tr class="bad"><td>$0.50</td><td>−0.77</td><td>−0.022</td><td>0.97</td></tr>
      <tr class="bad"><td>$0.50 + slip + 1-bar delay</td><td>−1.60</td><td>−0.044</td><td>0.94</td></tr>
    </tbody>
  </table></div>
</section>

<section class="block">
  <h2>Filters — each tested alone, none validated</h2>
  <p class="note">Every figure is <b>in-sample</b> on ≤36 trades and never combined. The best-looking
  one (min-box ≥ $8, +0.34R) is textbook overfitting. These are hypotheses for the larger study, not fixes.</p>
  <div class="tablewrap"><table>
    <thead><tr><th>Filter (alone)</th><th>N</th><th>Win%</th><th>PF</th><th>Expectancy</th></tr></thead>
    <tbody>
      <tr><td>Base (no filter)</td><td>36</td><td>36</td><td>1.23</td><td>+0.144</td></tr>
      <tr><td>Overnight-trend (with)</td><td>18</td><td>44</td><td>1.37</td><td>+0.204</td></tr>
      <tr><td>Min box ≥ $8</td><td>25</td><td>36</td><td>1.53</td><td>+0.338</td></tr>
      <tr><td>Break-even @ +1R</td><td>36</td><td>22</td><td>1.30</td><td>+0.116</td></tr>
      <tr><td>Trailing stop @ +1R</td><td>36</td><td>58</td><td>1.10</td><td>+0.038</td></tr>
      <tr><td>Partial TP half @ +1R</td><td>36</td><td>36</td><td>1.42</td><td>+0.164</td></tr>
    </tbody>
  </table></div>
</section>

<section class="block ceiling">
  <h2>Why only 39 days — and how to finish the job</h2>
  <p>The objective was 3–5 years of 1-minute data. In this environment that is <b>impossible</b>: the price
  feed caps 1-minute history at 30 days and blocks every institutional feed (Dukascopy, OANDA, stooq). The
  maximum defensible study here is 39 days at 5-minute resolution. That ceiling is the honest headline —
  no edge can be <i>certified</i> at this N regardless of result.</p>
  <p>The deliverable therefore ships <code>fetch_dukascopy.py</code>, a local-run kit that downloads real
  multi-year 1-minute gold data on an unconstrained machine and reruns this exact battery. <b>Decision rule
  for a real edge:</b> P(expectancy≤0) &lt; 0.05 · positive in ≥2 of 3 walk-forward windows · expectancy &gt; 0
  at $0.40/side · not dependent on one trade. Today's study fails all four.</p>
</section>

<footer><p>Reproducible from <code>data/</code> + <code>context.json</code>. Feed: COMEX GC=F via Yahoo v8.
  1-minute hammer approximated by 5-minute at the 39-day horizon; 20-day 1m run is the high-res cross-check.
  This is research, not financial advice.</p></footer>
</main>"""

STYLE = """
<style>
:root{
  --bg:#f5f6f8; --panel:#ffffff; --ink:#1a2230; --muted:#5b6675; --line:#dfe3e9;
  --accent:#2f5d8a; --accent-soft:#eaf1f8; --good:#2e8b57; --warn:#c98a1a; --bad:#c0392b;
  --shadow:0 1px 2px rgba(26,34,48,.06),0 4px 16px rgba(26,34,48,.05);
}
@media (prefers-color-scheme:dark){:root{
  --bg:#11151c; --panel:#181e28; --ink:#e6eaf0; --muted:#9aa5b4; --line:#28303c;
  --accent:#6fa8dc; --accent-soft:#1c2836; --good:#4cbb7f; --warn:#e0a94a; --bad:#e06a5a;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 22px rgba(0,0,0,.35);
}}
:root[data-theme="dark"]{
  --bg:#11151c; --panel:#181e28; --ink:#e6eaf0; --muted:#9aa5b4; --line:#28303c;
  --accent:#6fa8dc; --accent-soft:#1c2836; --good:#4cbb7f; --warn:#e0a94a; --bad:#e06a5a;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 22px rgba(0,0,0,.35);
}
:root[data-theme="light"]{
  --bg:#f5f6f8; --panel:#ffffff; --ink:#1a2230; --muted:#5b6675; --line:#dfe3e9;
  --accent:#2f5d8a; --accent-soft:#eaf1f8; --good:#2e8b57; --warn:#c98a1a; --bad:#c0392b;
  --shadow:0 1px 2px rgba(26,34,48,.06),0 4px 16px rgba(26,34,48,.05);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.55;-webkit-font-smoothing:antialiased}
main{max-width:1000px;margin:0 auto;padding:clamp(20px,4vw,52px) clamp(16px,4vw,32px);
  display:flex;flex-direction:column;gap:34px}
.mono,.val,td,th{font-variant-numeric:tabular-nums;
  font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
.eyebrow{font-family:ui-monospace,Menlo,monospace;font-size:.72rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--accent);margin-bottom:14px}
.hero h1{font-size:clamp(1.9rem,4.4vw,3rem);line-height:1.08;margin:0 0 16px;
  font-weight:750;letter-spacing:-.02em;text-wrap:balance;max-width:20ch}
.kill{color:var(--bad);font-style:italic}
.lede{font-size:1.08rem;color:var(--muted);max-width:66ch;margin:0 0 26px}
.verdict-row{display:flex;flex-wrap:wrap;gap:10px}
.v{display:flex;align-items:center;gap:9px;padding:9px 15px;border-radius:999px;
  border:1px solid var(--line);font-size:.86rem;color:var(--muted);background:var(--panel)}
.v .dot{width:9px;height:9px;border-radius:50%;background:var(--line)}
.v-fail{opacity:.6;text-decoration:line-through}
.v-on{color:#fff;background:var(--bad);border-color:var(--bad);font-weight:650}
.v-on .dot{background:#fff}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:16px 18px;box-shadow:var(--shadow)}
.stat.flag{border-color:var(--bad)}
.stat .k{font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.stat .val{font-size:1.85rem;font-weight:700;margin:6px 0 2px;letter-spacing:-.01em}
.stat .val .u{font-size:.9rem;color:var(--muted);margin-left:2px}
.stat .s{font-size:.78rem;color:var(--muted)}
.block h2{font-size:1.35rem;letter-spacing:-.01em;margin:0 0 16px;text-wrap:balance}
.tests{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
.test{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--bad);
  border-radius:10px;padding:16px 18px;box-shadow:var(--shadow)}
.test h3{margin:0 0 8px;font-size:.82rem;text-transform:uppercase;letter-spacing:.05em;color:var(--bad)}
.test p{margin:0;font-size:.92rem;color:var(--ink)}
.chart{width:100%;height:auto;border:1px solid var(--line);border-radius:12px;
  background:#fff;margin-bottom:16px;box-shadow:var(--shadow)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}
table{width:100%;border-collapse:collapse;font-size:.9rem;background:var(--panel)}
th,td{text-align:right;padding:11px 16px;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
thead th{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
  background:var(--accent-soft)}
tbody tr:last-child td{border-bottom:none}
tr.warn td{color:var(--warn)} tr.bad td{color:var(--bad);font-weight:600}
.note{font-size:.9rem;color:var(--muted);max-width:70ch;margin:0 0 16px}
.ceiling{background:var(--accent-soft);border:1px solid var(--line);border-radius:14px;
  padding:22px 24px}
.ceiling p{max-width:78ch;margin:0 0 12px}
code{font-family:ui-monospace,Menlo,monospace;font-size:.86em;background:var(--accent-soft);
  padding:2px 6px;border-radius:5px}
footer{border-top:1px solid var(--line);padding-top:18px}
footer p{font-size:.8rem;color:var(--muted);max-width:80ch;margin:0}
@media (prefers-reduced-motion:no-preference){.stat,.test{transition:transform .15s}
  .stat:hover,.test:hover{transform:translateY(-2px)}}
</style>"""

open("out/report.html", "w").write(STYLE + HTML)
print("-> out/report.html (", len(STYLE)+len(HTML), "bytes )")
