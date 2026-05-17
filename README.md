# Retirement Planner

A browser-based Monte Carlo retirement simulator. No server, no account — open the file and run.

## How it works

Each simulation draws random sequences of market returns, inflation, healthcare events, and longevity for both you and your spouse, then walks year by year tracking income, taxes, savings, withdrawals, and spending. Thousands of these runs produce a distribution of outcomes.

**Success** is defined as keeping liquid assets above the configured Minimum Liquid Buffer through end of life. Before a run is counted as failed, the model attempts several rescues: guardrails cut spending, and the vacation home is sold if one is held. A failure means all backstops were exhausted.

## Success rate targets

Because failures represent outcomes where every safeguard has already been tried, thresholds here are tighter than rules-of-thumb from simpler models:

| Color | Rate | Meaning |
|-------|------|---------|
| Green | ≥ 90% | Comfortable |
| Yellow | 80–89% | Warrants attention |
| Red | < 80% | Meaningful tail risk remains after all backstops |

## Key features

- **Stochastic returns and inflation** — drawn from configurable normal distributions each year
- **Dual income with independent growth** — primary and spouse income each have their own real growth mean, standard deviation, and floor
- **Retirement spending phases** — configurable living expense adjustment for early (≤75), mid (76–85), and late (86+) retirement
- **Guardrails** — spending adjusts year-by-year based on portfolio level relative to configurable thresholds
- **Tax modeling** — federal income tax, FICA, capital gains, RMDs, Roth conversions
- **Healthcare and LTC** — base healthcare costs plus stochastic long-term care events, with optional LTC insurance
- **Real estate** — primary home with mortgage amortization, optional vacation home with rental income and a configurable sell year
- **Windfalls** — recurring gifts, inheritance (probabilistic), and liquidity events (IPO/acquisition) with effective tax rate
- **Social Security** — configurable start age and haircut for policy uncertainty
- **Glide path** — optional equity-to-bond shift as retirement approaches

## Inputs

All dollar values are entered in **today's dollars**. The simulation inflates them internally each year using a stochastic inflation rate drawn from the configured distribution.

## Running locally

Open `index.html` in any modern browser. No build step, no dependencies.

## Charts

**Cash flow (10th percentile run)** — stacked annual expenses with income and net worth overlay for the 10th-percentile simulation, giving a view of a genuinely stressed but not catastrophic outcome.

**Min liquid buffer by percentile** — shows the lowest liquid portfolio value reached during retirement for each simulation, sorted worst to best. The x-axis extends 10 percentile points past the failure rate so the boundary between failing and surviving runs is visible in context. The line transitions continuously from red at the failure floor to green at twice that value.
