#!/bin/sh
# Serve both sites with their real Netlify headers, then run every check.
set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)

pkill -f "build/serve.py" 2>/dev/null || true
python3 build/serve.py sites/idlery 8801 >/tmp/srv-idlery.log 2>&1 &
python3 build/serve.py sites/corecredit 8802 >/tmp/srv-cc.log 2>&1 &
until curl -sf -o /dev/null http://127.0.0.1:8801/ && curl -sf -o /dev/null http://127.0.0.1:8802/; do :; done

status=0
echo "--- structure and local references ---"; python3 build/check.py || status=1
echo; echo "--- colour contrast ---"; python3 build/contrast.py | tail -2 || status=1
echo; echo "--- content sweep ---"; python3 build/check_content.py || status=1
echo; echo "--- browser: CSP, overflow, tap targets, large text ---"
cp build/verify_browser.mjs /home/user/.webtools/
( cd /home/user/.webtools && node verify_browser.mjs idlery=http://127.0.0.1:8801 corecredit=http://127.0.0.1:8802 ) || status=1

pkill -f "build/serve.py" 2>/dev/null || true
exit $status
