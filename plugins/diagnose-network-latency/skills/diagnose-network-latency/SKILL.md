---
name: diagnose-network-latency
description: >-
  Diagnose slow, laggy, or flaky internet on macOS — measures latency, jitter,
  packet loss, Wi-Fi signal quality, DNS speed, throughput, and VPN overhead, then
  pinpoints the root cause (interference, channel congestion, weak signal, VPN, DNS,
  or ISP). Use this WHENEVER the user reports that the internet/Wi-Fi feels slow,
  laggy, has "latency", keeps dropping, lags on video calls or SSH, or asks to
  "check the wifi", "check the network", "test my connection", or "why is my
  internet bad" — even if they don't name a specific tool or metric. Also use to
  inspect the current home/network configuration on a Mac.
---

# Diagnose network latency (macOS)

## What this does

A connection can "feel laggy" for reasons that a single speed test or one quick
ping completely miss. The usual culprits are **jitter** (latency that swings
wildly even when the average looks fine), **intermittent packet loss**, a **weak
or congested Wi-Fi channel**, **slow DNS**, or a **VPN** adding overhead on top of
everything. This skill gathers all of those signals in one pass and then reasons
about which one is actually responsible.

## Your environment

This skill was built for a specific home setup. Use these facts to skip rediscovery and
point recommendations at the right place — but always confirm against live probe output,
since hardware and VPN state change.

- **Router: NETGEAR Orbi MR60** (Orbi WiFi 6 / AX1800) **mesh**, run as a 3-piece system:
  the MR60 router plus two satellites. On the LAN they appear as `10.0.0.1` (gateway),
  `10.0.0.5`, and `10.0.0.16`, all with the NETGEAR `34:98:b5` MAC prefix.
- **LAN: `10.0.0.0/24`**, physical Wi-Fi on `en0` (5 GHz, channel 153/80 MHz, 802.11ax).
  The network is dense with IoT (Espressif/Tuya/TP-Link smart-home gear, robot vacuums,
  a Peloton, a Nintendo Switch) plus several Apple devices and phones on randomized MACs.
- **Corporate VPN on `utun5`** frequently owns the default route, tunneling ALL traffic.
  This is a prime latency/throughput suspect — factor it in, and suggest a VPN-off re-run
  to separate VPN overhead from home-network problems.

**Where per-device bandwidth actually lives (the "who's hogging the wifi" answer):**
The Mac can't see other devices' traffic, but the Orbi can. Direct the user to:
1. **NETGEAR Orbi app** → *Devices* → tap a device for **live up/down throughput**; sort to
   find the hog, and *pause* it to confirm (watch latency recover). This is the best tool.
2. **Web admin** at `http://orbilogin.com` (or `routerlogin.net`), login `admin` →
   *Attached Devices* for the full list with editable friendly names (great for naming the
   devices `--scan` can only identify by vendor), and *Advanced → Traffic Meter* for total
   WAN usage over time.
3. *Historical* per-device usage generally needs a **NETGEAR Armor** subscription; the live
   view is free and enough to catch an active hog.

## How to run it

Run the bundled probe. It prints a report and appends one row to a history CSV so
repeated runs reveal trends:

```bash
~/.claude/skills/diagnose-network-latency/scripts/netdiag.sh
```

Useful flags:
- `--count N` — number of pings in the sustained test (default 30; raise to 100 to hunt rare spikes)
- `--no-speedtest` — skip the 25 MB download test (faster, no data used)
- `--target HOST` — change the primary internet ping target (default `8.8.8.8`)
- `--history PATH` — point the history log somewhere else
- `--scan` — inventory every device on the LAN (ping sweep + ARP + MAC-vendor lookup)
  instead of running the latency probe. Use this when the user suspects "a device is
  hogging the wifi" or asks what's connected. It identifies each device by manufacturer
  using a locally-cached public OUI database (no MAC addresses are sent anywhere) and
  flags randomized/private MACs. It does NOT measure per-device bandwidth — that's
  physically impossible from this host on encrypted Wi-Fi; see § Your environment for
  where the per-device usage actually lives.

The script needs no `sudo`. It works on macOS 14+ where Apple removed the old
`airport` binary — Wi-Fi facts come from `system_profiler SPAirPortDataType`.

After it runs, **interpret the numbers** using the thresholds below and give the
user a short verdict + concrete next steps. Don't just dump the raw output.

## How to read the results

Think of it as a path: the packet leaves the Mac, crosses Wi-Fi to the router,
maybe enters a VPN tunnel, traverses the ISP, and reaches the target. A problem at
any hop shows up differently. Work through these.

### Latency & jitter (the usual answer)
- **avg latency**: <30 ms great, 30–60 ms okay, >100 ms sluggish for interactive use.
- **jitter (stddev)**: this is the one that makes things *feel* broken. <5 ms is
  smooth; >20 ms, or a `max` several times the `min`, means the link is unstable
  even if the average looks fine. High jitter with **0% loss** points at Wi-Fi
  airtime contention or interference rather than the ISP.
- **packet loss**: anything above 0–1% is a real problem. Loss + high jitter
  together usually means a saturated or interfered Wi-Fi link.
- Compare the two targets (8.8.8.8 vs 1.1.1.1): if both are equally bad, the issue
  is local (Wi-Fi/VPN/ISP); if only one is bad, it's a path/peering issue out on
  the internet and nothing the user can fix.

### Wi-Fi signal
- **RSSI**: −50 dBm excellent, −60 good, −67 the edge of reliable, −70+ weak.
  Weak signal forces retransmits, which is a top cause of jitter.
- **SNR** (signal minus noise): >25 dB is healthy; <20 dB means noise is eating the
  link — move closer, or a neighbor/appliance is interfering.
- **Channel**: 2.4 GHz is crowded and slow; 5 GHz is better. On 5 GHz, an 80 MHz
  channel that overlaps a busy neighboring network causes bursty spikes — moving
  to a less crowded channel or narrowing to 40 MHz often fixes intermittent lag.
- **TX rate** far below the PHY-mode maximum is a sign of a poor link (distance,
  obstruction, interference).

### VPN (easy to overlook)
If the report flags a **VPN TUNNEL** on the default route, the VPN is carrying all
traffic and adds its own latency, jitter, and throughput overhead. This is often
the real reason a connection "feels slow" while the underlying Wi-Fi is fine. To
confirm, suggest the user briefly disconnect the VPN and re-run — if latency and
throughput jump back, the VPN (or its concentrator/server load) is the bottleneck,
not their home network.

### DNS
- A first (uncached) lookup over ~100 ms makes everything feel slow to *start* even
  when the connection is fast. If DNS is the outlier, suggest switching resolver to
  1.1.1.1 or 8.8.8.8. (Note: a VPN may force its own DNS.)

### Throughput
- Compare download Mbps against the user's expected plan AND against the Wi-Fi TX
  rate. A download far below both a fast link rate and the plan suggests VPN
  overhead, ISP throttling, or a congested channel — not raw Wi-Fi reach.

## Reporting back

Lead with the verdict, then the evidence, then the fix. Something like:

```
Diagnosis: <one-line root cause>

Evidence:
  - <the 1–3 metrics that prove it>

Try this:
  1. <most likely fix>
  2. <next>
```

Keep it tight. The user wants to know *what's wrong* and *what to do*, not read a
networking lecture.

## Tracking trends over time

Because this is usually a *recurring* complaint, the history CSV is the real payoff.
To see whether things are getting worse, when spikes happen, or whether the VPN
correlates with bad runs:

```bash
column -s, -t < ~/.cache/netdiag/history.csv | less -S
```

If the user reports the problem "again", run a fresh probe and compare against past
rows — e.g. jitter creeping up over weeks points at a failing AP or a new source of
interference; bad runs only when `vpn=1` confirm the VPN. Suggest running the probe
at a few different times of day to catch time-correlated congestion.
