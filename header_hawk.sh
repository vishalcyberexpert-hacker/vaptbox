#!/bin/bash
clear

# ================= INTRO BANNER =================
toilet -f mono12 -F metal -W HEADER | lolcat || true
toilet -f mono12 -F metal -W HAWK | lolcat || true
echo "NEXT-GEN HEADER ANALYSIS TOOLKIT" | lolcat
cowsay -f dragon-and-cow vishal.cyberexpert@gmail.com | lolcat || true

# ================= COLORS =================
green="\033[38;5;82m"
yellow="\033[38;5;220m"
blue="\033[38;5;51m"
red="\033[38;5;196m"
reset="\033[0m"

# ================= INPUT =================
echo -ne "$(echo 'ENTER TARGET URL (https://example.com): ' | lolcat)"
read TARGET

DOMAIN=$(echo "$TARGET" | sed 's~http[s]*://~~' | sed 's~/.*~~')

DATE=$(date +"%Y-%m-%d_%H-%M-%S")
OUTDIR="reports/$DOMAIN/$DATE"
mkdir -p "$OUTDIR"

LOG="$OUTDIR/full_report.log"

# ================= GLOBAL LOGGER =================
exec > >(tee -a "$LOG" | ts '[%Y-%m-%d %a %H:%M:%S]') 2>&1

COUNT=0
run() {
  ((COUNT++))
  eval "$1" 2>&1 | ts '[%Y-%m-%d %a %H:%M:%S]' | tee -a "$2" || true
}

echo -e "${green}FULL HTTP HEADER & CLIENT-SIDE SECURITY ANALYSIS${reset}"
echo "================================================================="

# ================= BASE HEADER COLLECTION (ONCE) =================
BASE_HEADERS="$OUTDIR/01_base_headers.txt"
REDIRECT_HEADERS="$OUTDIR/01_redirect_headers.txt"

run "curl -s -D - -o /dev/null $TARGET" "$BASE_HEADERS"
run "curl -s -L -D - -o /dev/null $TARGET" "$REDIRECT_HEADERS"

# ================= SECURITY HEADERS (CORE CHECK) =================
SEC="$OUTDIR/02_security_headers.txt"
grep -Ei \
"content-security-policy|strict-transport-security|x-frame-options|x-content-type-options|referrer-policy|permissions-policy" \
"$BASE_HEADERS" | tee -a "$SEC" || true

# ================= CSP =================
CSP="$OUTDIR/03_csp.txt"
grep -i "content-security-policy" "$BASE_HEADERS" | tee -a "$CSP" || true
run "curl -I $TARGET/wp-login.php | grep -i content-security-policy" "$CSP"

# ================= HSTS =================
HSTS="$OUTDIR/04_hsts.txt"
grep -i strict-transport-security "$BASE_HEADERS" | tee -a "$HSTS" || true
run "curl -I http://$DOMAIN" "$HSTS"

# ================= CLICKJACKING =================
CLICK="$OUTDIR/05_clickjacking.txt"
grep -Ei "x-frame-options|content-security-policy" "$BASE_HEADERS" | tee -a "$CLICK" || true

# ================= MIME SNIFFING =================
MIME="$OUTDIR/06_mime_sniffing.txt"
grep -i x-content-type-options "$BASE_HEADERS" | tee -a "$MIME" || true

# ================= REFERRER POLICY =================
REF="$OUTDIR/07_referrer_policy.txt"
grep -i referrer-policy "$BASE_HEADERS" | tee -a "$REF" || true

# ================= PERMISSIONS POLICY =================
PERM="$OUTDIR/08_permissions_policy.txt"
grep -i permissions-policy "$BASE_HEADERS" | tee -a "$PERM" || true

# ================= CACHE & COOKIES =================
CACHE="$OUTDIR/09_cache_cookies.txt"
grep -Ei \
"cache-control|pragma|expires|set-cookie|httponly|secure|samesite" \
"$BASE_HEADERS" | tee -a "$CACHE" || true

# ================= SERVER / PLATFORM DISCLOSURE =================
SERVER="$OUTDIR/10_server_disclosure.txt"
grep -Ei \
"server|x-powered-by|via|platform|panel" \
"$BASE_HEADERS" | tee -a "$SERVER" || true

# ================= HTTP METHODS =================
METHODS="$OUTDIR/11_http_methods.txt"
run "curl -X OPTIONS -I $TARGET" "$METHODS"
run "nmap -p 80,443 --script http-methods $DOMAIN" "$METHODS"

# ================= HEADER INJECTION =================
INJECT="$OUTDIR/12_header_injection.txt"
run "curl -H \$'X-Test: test\\r\\nInjected: yes' -I $TARGET" "$INJECT"
run "curl -H 'Host: evil.com' -I $TARGET" "$INJECT"

# ================= IP SPOOFING =================
IP="$OUTDIR/13_ip_spoofing.txt"
run "curl -H 'X-Forwarded-For: 127.0.0.1' -I $TARGET" "$IP"
run "curl -H 'X-Client-IP: 127.0.0.1' -I $TARGET" "$IP"
run "curl -H 'X-Real-IP: 127.0.0.1' -I $TARGET" "$IP"

# ================= HTTP DESYNC =================
DESYNC="$OUTDIR/14_http_desync.txt"
run "printf \"POST / HTTP/1.1\r\nHost: $DOMAIN\r\nContent-Length: 4\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n\" | nc $DOMAIN 80" "$DESYNC"

# ================= TLS / CERT / HSTS CONTEXT =================
TLS="$OUTDIR/15_tls_context.txt"
run "openssl s_client -connect $DOMAIN:443 -servername $DOMAIN" "$TLS"

# ================= AUTOMATED CONTEXT =================
AUTO="$OUTDIR/16_automated_context.txt"
run "nmap -p 80,443 --script http-security-headers $DOMAIN" "$AUTO"
run "nikto -h $TARGET" "$AUTO"
run "whatweb -v $TARGET" "$AUTO"

# ================= SUMMARY =================
echo -e "\n${green}SCAN COMPLETED SUCCESSFULLY${reset}"
echo -e "${yellow}TOTAL COMMANDS EXECUTED: $COUNT${reset}"
echo -e "${green}REPORT LOCATION:${reset} $OUTDIR"
