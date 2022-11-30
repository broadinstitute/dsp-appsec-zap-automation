#/bin/bash

/zap/zap.sh -Xmx10g -host 127.0.0.1 -port 8081 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true -config api.disablekey=true -daemon &>/dev/null
python3 scan.py
exit
