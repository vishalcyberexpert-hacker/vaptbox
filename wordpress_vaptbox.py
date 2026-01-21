#!/usr/bin/env python3
import os
import sys
import time
import random
from datetime import datetime
import subprocess

# =========================
# FULL-SCREEN INTRO ANIMATION (ADDED – 10s)
# =========================
w = os.get_terminal_size().columns
h = os.get_terminal_size().lines
os.system("clear")

text = " VISHAL CYBER EXPERT "
pad = (w - len(text)) // 2

start = time.time()
while time.time() - start < 10:
    screen = []
    for i in range(h):
        if i % 3 == 0:
            line = (
                "".join(random.choice("█▓▒░01") for _ in range(pad)) +
                text +
                "".join(random.choice("█▓▒░01") for _ in range(w))
            )
            screen.append(line[:w])
        else:
            screen.append("".join(random.choice("█▓▒░01") for _ in range(w)))
    print("\n".join(screen))
    time.sleep(0.05)

# =========================
# COLORS (for internal use)
# =========================
green = "\033[38;5;82m"
yellow = "\033[38;5;226m"
blue = "\033[38;5;51m"
reset = "\033[0m"

# =========================
# BANNER
# =========================
os.system("clear")
os.system("toilet -f mono12 -F metal -W WORD | lolcat")
os.system("toilet -f mono12 -F metal -W PRESS | lolcat")
os.system("toilet -f mono12 -F metal -W VAPTBOX | lolcat")
os.system(f"echo 'NEXT-GEN WORDPRESS VAPT AUTOMATOR' | lolcat")
os.system("cowsay -f dragon-and-cow vishal.cyberexpert@gmail.com | lolcat")

# =========================
# INPUT (all prompts via lolcat)
# =========================
def lolcat_input(prompt):
    os.system(f"echo '{prompt}' | lolcat")
    return input().strip()

TARGET = lolcat_input("TARGET (http/https):")
WORDLIST = lolcat_input("DIR WORDLIST [default]:")
USERLIST = lolcat_input("USER WORDLIST [default]:")
PASSLIST = lolcat_input("PASS WORDLIST [default]:")
THREADS = lolcat_input("MAX THREADS:")
APITOKEN = lolcat_input("WPSCAN API TOKEN (optional):")

WORDLIST = WORDLIST or "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"
USERLIST = USERLIST or "/usr/share/wordlists/seclists/Usernames/top-usernames-shortlist.txt"
PASSLIST = PASSLIST or "/usr/share/wordlists/rockyou.txt"
THREADS = THREADS or "20"

DOMAIN = TARGET.replace("http://", "").replace("https://", "").split("/")[0]
OUTDIR = f"wp_scan_{datetime.now().strftime('%F_%H-%M-%S')}"
os.makedirs(OUTDIR, exist_ok=True)
LOGFILE = f"{OUTDIR}/output.log"

COUNT = 0

# =========================
# RUN FUNCTION (only show command in lolcat, suppress output)
# =========================
def run(cmd):
    global COUNT
    COUNT += 1
    # Show command being run in lolcat
    os.system(f"echo '[{COUNT}] Running: {cmd}' | lolcat")
    # Run the command, suppress stdout/stderr, but log it
    with open(LOGFILE, "a") as logf:
        subprocess.run(cmd, shell=True, stdout=logf, stderr=logf)
    os.system(f"echo '--------------------------------------------------------------------------------' | lolcat")

# =========================
# 1. FOOTPRINT + WEB INFO
# =========================
run(f"dig {DOMAIN}")
run(f"nslookup {DOMAIN}")
run(f"ping -c 4 {DOMAIN}")
run(f"traceroute {DOMAIN}")
run(f"curl -I {TARGET}")
run(f"whatweb {TARGET}")

# =========================
# 2. NMAP
# =========================
run(f"nmap -p- {DOMAIN}")
run(
    f"nmap -p 80,443 -sC -sV "
    f"--script http-headers,http-enum,http-robots.txt,http-sitemap-generator,http-generator,"
    f"http-wordpress-enum,http-wordpress-users,http-config-backup,ssl-cert,ssl-enum-ciphers {DOMAIN} || true"
)

# =========================
# 3. WORDPRESS FILE CHECKS
# =========================
URLS = [
    "readme.html", "wp-admin/", "wp-login.php", "xmlrpc.php", "wp-json/",
    "wp-content/", "wp-content/plugins/", "wp-content/themes/",
    "wp-content/uploads/", "wp-includes/", "debug.log", "error.log",
    "wp-config.php~", "wp-config.bak", "?author=1", "?author=2",
    "author/admin/", "backup/", "site.zip", "db.sql",
    "feed/", "comments/feed/"
]

for u in URLS:
    run(f'curl -s -o /dev/null -w "%{{http_code}} {u}\\n" {TARGET}/{u}')

# =========================
# 4. DIRECTORY ENUM
# =========================
run(f"gobuster dir -u {TARGET} -w {WORDLIST} -t {THREADS} -s 200,204,301,302,307,401,403")
run(f"dirsearch -u {TARGET} -w {WORDLIST} -t {THREADS}")

# =========================
# 5. REST API ENUM
# =========================
run(f"curl {TARGET}/wp-json/wp/v2/users")
run(f"curl {TARGET}/wp-json/wp/v2/posts")
run(f"curl {TARGET}/wp-json/wp/v2/media")

# =========================
# 6. WPSCAN FULL ENUM
# =========================
if APITOKEN:
    run(
        f"wpscan --url {TARGET} "
        f"--api-token {APITOKEN} "
        f"--enumerate vp,vt,cb,dbe,v "
        f"--plugins-detection aggressive "
        f"--themes-detection aggressive "
        f"--max-threads {THREADS} "
        f"--random-user-agent "
        f"--no-update --force"
    )

# =========================
# 7. USER ENUM
# =========================
run(f"wpscan --url {TARGET} --enumerate u --no-update --force")

# =========================
# 8. BRUTE FORCE (DUAL MODE)
# =========================
run(
    f"wpscan --url {TARGET} "
    f"--usernames {USERLIST} "
    f"--passwords {PASSLIST} "
    f"--password-attack xmlrpc "
    f"--max-threads {THREADS} "
    f"--no-update --force"
)

run(
    f"wpscan --url {TARGET} "
    f"--usernames {USERLIST} "
    f"--passwords {PASSLIST} "
    f"--max-threads {THREADS} "
    f"--no-update --force"
)

# =========================
# 9. FINAL REPORT
# =========================
run(f"wpscan --url {TARGET} -o {OUTDIR}/wpscan.txt --no-update --force")
run(f"wpscan --url {TARGET} --format json -o {OUTDIR}/wpscan.json --no-update --force")

os.system(f"echo '\nTOTAL COMMANDS EXECUTED: {COUNT}' | lolcat")
os.system("cowsay -f kiss SCAN COMPLETED | lolcat")
