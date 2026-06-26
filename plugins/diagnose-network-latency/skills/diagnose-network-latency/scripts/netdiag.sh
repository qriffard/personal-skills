#!/usr/bin/env bash
#
# netdiag.sh — one-shot network latency / jitter / signal / throughput probe for macOS.
#
# Gathers everything the diagnose-network-latency skill needs in a single run, prints a
# human-readable report, and appends one CSV row to the history log so patterns over time
# are visible. Designed for macOS 14+ where the old `airport` binary was removed — Wi-Fi
# facts come from `system_profiler SPAirPortDataType` instead.
#
# Usage:
#   netdiag.sh [--count N] [--no-speedtest] [--target HOST] [--history PATH]
#
# Flags:
#   --count N        number of pings in the sustained latency test (default 30)
#   --no-speedtest   skip the download throughput test (faster, no data usage)
#   --target HOST    primary internet ping target (default 8.8.8.8)
#   --history PATH   override the history CSV location
#
# Exit code is always 0 on a completed run; "problems" are reported in the text, not the
# exit status, so a caller can read the report regardless.

set -u

# ---- config / args -----------------------------------------------------------
COUNT=30
DO_SPEEDTEST=1
TARGET="8.8.8.8"
TARGET2="1.1.1.1"
HISTORY="${HOME}/.cache/netdiag/history.csv"

SCAN=0
OUI_DB="${HOME}/.cache/netdiag/manuf"

while [ $# -gt 0 ]; do
  case "$1" in
    --count) COUNT="$2"; shift 2 ;;
    --no-speedtest) DO_SPEEDTEST=0; shift ;;
    --target) TARGET="$2"; shift 2 ;;
    --history) HISTORY="$2"; shift 2 ;;
    --scan) SCAN=1; shift ;;
    *) echo "unknown arg: $1" >&2; shift ;;
  esac
done

mkdir -p "$(dirname "$HISTORY")" 2>/dev/null
NOW="$(date '+%Y-%m-%d %H:%M:%S')"

# ---- helpers -----------------------------------------------------------------
# Pull "key: value" out of an indented system_profiler / ipconfig block.
field() { awk -F': ' -v k="$1" '$0 ~ k"$"||$0 ~ k": " {sub(/^[ \t]*[^:]*: /,""); print; exit}'; }

# Look up a MAC's manufacturer from the cached Wireshark OUI database. Returns "" if the
# DB is missing or the prefix isn't found. Matching is local — no MAC ever leaves the host.
oui_vendor() {
  [ -f "$OUI_DB" ] || return 0
  # Normalize the first three octets to the DB's "XX:XX:XX" uppercase form, zero-padding
  # single-hex-digit octets (arp prints e.g. "4:99:b9", the DB stores "04:99:B9"). We pad
  # in bash via printf's 0x-hex handling — macOS's default awk has no strtonum().
  local a b c pfx
  IFS=: read -r a b c _ <<EOF
$1
EOF
  pfx="$(printf '%02X:%02X:%02X' "0x$a" "0x$b" "0x$c" 2>/dev/null)"
  [ -z "$pfx" ] && return 0
  grep -i -m1 "^${pfx}[[:space:]]" "$OUI_DB" | awk -F'\t' '{print ($3!=""?$3:$2)}'
}

# ---- device scan (--scan): inventory every device on the local LAN ------------
# Per-device *bandwidth* can't be measured from this host on encrypted Wi-Fi — only the
# router sees that. What we CAN do is enumerate who's on the network and identify each by
# MAC vendor, which is the first step to spotting an unexpected or hoggy device.
if [ "$SCAN" = "1" ]; then
  WP="$(networksetup -listallhardwareports 2>/dev/null | awk '/Wi-Fi|AirPort/{getline; print $2; exit}')"
  WIP="$(ipconfig getifaddr "$WP" 2>/dev/null)"
  if [ -z "$WIP" ]; then echo "No Wi-Fi IP found on ${WP:-Wi-Fi}; is Wi-Fi connected?"; exit 0; fi
  PREFIX="${WIP%.*}"   # assume the common /24; covers virtually all home LANs

  # Refresh the OUI DB if it's missing or older than ~30 days, so vendor names stay current
  # without re-downloading every run. One public file fetch; no per-device API calls.
  if [ ! -f "$OUI_DB" ] || [ -n "$(find "$OUI_DB" -mtime +30 2>/dev/null)" ]; then
    echo "Updating OUI vendor database..."
    curl -s --max-time 30 -o "$OUI_DB" "https://www.wireshark.org/download/automated/data/manuf" 2>/dev/null \
      || echo "  (couldn't fetch OUI DB — vendors will show as unknown)"
  fi

  echo "Scanning ${PREFIX}.0/24 on ${WP} (~10s)..."
  for i in $(seq 1 254); do ping -c1 -W200 -t1 "${PREFIX}.${i}" >/dev/null 2>&1 & done
  wait 2>/dev/null

  echo
  printf "%-14s %-19s %s\n" "IP" "MAC" "VENDOR / NOTE"
  printf "%-14s %-19s %s\n" "----" "---" "-------------"
  arp -an -i "$WP" 2>/dev/null \
    | grep -v -E "incomplete|ff:ff:ff:ff:ff:ff|\(224\.|\(239\.|\.255\)" \
    | sed -E 's/.*\(([0-9.]+)\) at ([0-9a-f:]+) .*/\1 \2/' \
    | sort -u -t. -k4 -n \
    | while read -r ip mac; do
        [ -z "$mac" ] && continue
        # A set 0x02 bit in the first octet marks a locally-administered (randomized) MAC,
        # which modern phones use for privacy — vendor lookup is meaningless for those.
        first=$(printf '%d' "0x${mac%%:*}" 2>/dev/null)
        if [ -n "$first" ] && [ $(( first & 2 )) -ne 0 ]; then
          note="randomized MAC (private Wi-Fi — likely a phone)"
        else
          note="$(oui_vendor "$mac")"; [ -z "$note" ] && note="unknown vendor"
        fi
        [ "$ip" = "$WIP" ] && note="THIS MAC"
        printf "%-14s %-19s %s\n" "$ip" "$mac" "$note"
      done
  echo
  echo "Note: this lists WHO is on the network. To see which device is using the most"
  echo "bandwidth, open the router's app/admin — your Mac can't measure other devices'"
  echo "traffic on encrypted Wi-Fi. See SKILL.md § Your environment for the exact path."
  exit 0
fi

# ---- active interface --------------------------------------------------------
# The default route's interface is what traffic actually uses. On a machine with a
# corporate/personal VPN this is often a tunnel (utunN), NOT the physical NIC — which
# matters a lot, because a VPN adds its own latency and overhead on top of the link.
IFACE="$(route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
GW="$(route -n get default 2>/dev/null | awk '/gateway:/{print $2; exit}')"
[ -z "$IFACE" ] && IFACE="(none)"

# Detect a VPN tunnel carrying the default route. utunN is the macOS userspace-tunnel
# convention used by the built-in VPN client, WireGuard, Tailscale, corporate clients, etc.
VPN_ACTIVE=0
case "$IFACE" in utun*|ppp*|ipsec*) VPN_ACTIVE=1 ;; esac

# The physical Wi-Fi device (e.g. en0) — independent of which route is default, so we can
# still read real signal quality even when a VPN owns the default route.
WIFI_PORT="$(networksetup -listallhardwareports 2>/dev/null \
  | awk '/Wi-Fi|AirPort/{getline; print $2; exit}')"
WIFI_IP="$(ipconfig getifaddr "$WIFI_PORT" 2>/dev/null)"
# Treat Wi-Fi as present if the Wi-Fi NIC has an address, regardless of the default route.
IS_WIFI=0
[ -n "$WIFI_PORT" ] && [ -n "$WIFI_IP" ] && IS_WIFI=1

# ---- Wi-Fi signal (system_profiler; airport is gone on macOS 14+) ------------
RSSI=""; NOISE=""; SNR=""; CHANNEL=""; PHY=""; TXRATE=""; SSID=""
if [ "$IS_WIFI" = "1" ]; then
  WINFO="$(system_profiler SPAirPortDataType 2>/dev/null \
    | awk '/Current Network Information:/{f=1} f{print} /Other Local Wi-Fi/{exit}')"
  SSID="$(printf '%s\n' "$WINFO" | awk 'NR==2{gsub(/[: ]*$/,""); sub(/^[ \t]*/,""); print; exit}')"
  PHY="$(printf '%s\n' "$WINFO" | field 'PHY Mode')"
  CHANNEL="$(printf '%s\n' "$WINFO" | field 'Channel')"
  TXRATE="$(printf '%s\n' "$WINFO" | field 'Transmit Rate')"
  SIGNAL="$(printf '%s\n' "$WINFO" | field 'Signal / Noise')"
  # Signal / Noise looks like "-59 dBm / -94 dBm"
  RSSI="$(printf '%s\n' "$SIGNAL" | awk '{print $1}')"
  NOISE="$(printf '%s\n' "$SIGNAL" | awk '{print $4}')"
  if [ -n "$RSSI" ] && [ -n "$NOISE" ]; then
    SNR=$(( RSSI - NOISE ))
  fi
fi

# ---- sustained latency / jitter ----------------------------------------------
# A single quick ping hides the spikes that make a link "feel" laggy. A sustained
# run surfaces jitter (stddev) and intermittent loss, which is usually the real story.
PSTAT="$(ping -c "$COUNT" -i 0.3 "$TARGET" 2>/dev/null)"
LOSS="$(printf '%s\n' "$PSTAT" | awk -F', ' '/packet loss/{for(i=1;i<=NF;i++) if($i ~ /packet loss/){sub(/ packet loss.*/,"",$i); print $i}}')"
RTT="$(printf '%s\n' "$PSTAT" | awk -F' = ' '/round-trip|rtt/{print $2}')"
PMIN="$(printf '%s\n' "$RTT" | awk -F'/' '{print $1}')"
PAVG="$(printf '%s\n' "$RTT" | awk -F'/' '{print $2}')"
PMAX="$(printf '%s\n' "$RTT" | awk -F'/' '{print $3}')"
PDEV="$(printf '%s\n' "$RTT" | awk -F'/' '{print $4}' | awk '{print $1}')"

# Second target distinguishes "the whole internet" from "one provider's path".
PAVG2="$(ping -c 5 "$TARGET2" 2>/dev/null | awk -F' = ' '/round-trip|rtt/{print $2}' | awk -F'/' '{print $2}')"

# ---- gateway reachability ----------------------------------------------------
# Many routers firewall ICMP, so "no reply" here is informational, not a verdict.
GW_RESULT="n/a"
if [ -n "$GW" ]; then
  GW_LOSS="$(ping -c 3 -t 2 "$GW" 2>/dev/null | awk -F', ' '/packet loss/{for(i=1;i<=NF;i++) if($i ~ /packet loss/){sub(/ packet loss.*/,"",$i); print $i}}')"
  GW_RTT="$(ping -c 3 -t 2 "$GW" 2>/dev/null | awk -F' = ' '/round-trip|rtt/{print $2}' | awk -F'/' '{print $2}')"
  if [ -n "$GW_RTT" ]; then GW_RESULT="${GW_RTT} ms (${GW_LOSS} loss)"; else GW_RESULT="no ICMP reply (often firewalled — usually fine)"; fi
fi

# ---- DNS timing --------------------------------------------------------------
# Slow name resolution feels like latency but is a different fault than a slow path.
DNS_MS="$(/usr/bin/time -p dscacheutil -q host -a name apple.com >/dev/null 2>/tmp/.netdiag_dns; awk '/real/{printf "%.0f", $2*1000}' /tmp/.netdiag_dns)"
rm -f /tmp/.netdiag_dns 2>/dev/null

# ---- throughput (optional) ---------------------------------------------------
DL_MBPS=""
if [ "$DO_SPEEDTEST" = "1" ]; then
  # Cloudflare's speed endpoint serves arbitrary-size payloads; 25 MB is enough to
  # get a stable number without burning much data. We read curl's measured speed.
  BYTES=25000000
  SPEED_BPS="$(curl -s -o /dev/null -w '%{speed_download}' --max-time 30 \
    "https://speed.cloudflare.com/__down?bytes=${BYTES}" 2>/dev/null)"
  if [ -n "$SPEED_BPS" ] && [ "${SPEED_BPS%.*}" -gt 0 ] 2>/dev/null; then
    DL_MBPS="$(awk -v b="$SPEED_BPS" 'BEGIN{printf "%.1f", b*8/1000000}')"
  fi
fi

# ---- report ------------------------------------------------------------------
echo "=============================================="
echo " Network diagnostic — ${NOW}"
echo "=============================================="
echo "Default route:    ${IFACE}$([ "$VPN_ACTIVE" = 1 ] && echo '  ⚠️  VPN TUNNEL — all traffic is going through a VPN')"
[ -n "$GW" ] && echo "Gateway:          ${GW}"
if [ "$VPN_ACTIVE" = "1" ] && [ "$IS_WIFI" = "1" ]; then
  echo "Physical link:    ${WIFI_PORT} (Wi-Fi, ${WIFI_IP}) — the VPN runs on top of this"
fi
echo
if [ "$IS_WIFI" = "1" ]; then
  echo "--- Wi-Fi signal (${WIFI_PORT}) ---"
  [ -n "$SSID" ]    && echo "  SSID:           ${SSID}"
  [ -n "$RSSI" ]    && echo "  Signal (RSSI):  ${RSSI} dBm"
  [ -n "$NOISE" ]   && echo "  Noise:          ${NOISE} dBm"
  [ -n "$SNR" ]     && echo "  SNR:            ${SNR} dB"
  [ -n "$CHANNEL" ] && echo "  Channel:        ${CHANNEL}"
  [ -n "$PHY" ]     && echo "  PHY mode:       ${PHY}"
  [ -n "$TXRATE" ]  && echo "  TX rate:        ${TXRATE} Mbps"
  echo
fi
echo "--- Latency to ${TARGET} (${COUNT} pings) ---"
echo "  min/avg/max:    ${PMIN:-?} / ${PAVG:-?} / ${PMAX:-?} ms"
echo "  jitter (stddev):${PDEV:-?} ms"
echo "  packet loss:    ${LOSS:-?}"
[ -n "$PAVG2" ] && echo "  (avg to ${TARGET2}: ${PAVG2} ms)"
echo
echo "--- Other checks ---"
echo "  Gateway:        ${GW_RESULT}"
echo "  DNS lookup:     ${DNS_MS:-?} ms"
[ "$DO_SPEEDTEST" = "1" ] && echo "  Download:       ${DL_MBPS:-failed} Mbps"
echo

# ---- history log -------------------------------------------------------------
if [ ! -f "$HISTORY" ]; then
  echo "timestamp,interface,vpn,rssi_dbm,noise_dbm,snr_db,channel,tx_rate_mbps,ping_min_ms,ping_avg_ms,ping_max_ms,jitter_ms,loss,dns_ms,download_mbps" > "$HISTORY"
fi
echo "${NOW},${IFACE},${VPN_ACTIVE},${RSSI},${NOISE},${SNR},\"${CHANNEL}\",${TXRATE},${PMIN},${PAVG},${PMAX},${PDEV},${LOSS},${DNS_MS},${DL_MBPS}" >> "$HISTORY"
echo "History appended → ${HISTORY}"
echo "(run with the same command over time to compare; the SKILL.md explains how to read trends)"
