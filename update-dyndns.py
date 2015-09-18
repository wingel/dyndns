#! /usr/bin/python
from __future__ import print_function

import sys
from netifaces import ifaddresses, AF_INET

import dns.name
import dns.message
import dns.query
import dns.query
import dns.tsigkeyring
import dns.update

force = 0

def main():
    nameserver = sys.argv[1]
    zone = sys.argv[2]
    name = sys.argv[3]
    interface = sys.argv[4]
    keyfn = sys.argv[5]

    actual = []
    for d in ifaddresses(interface).setdefault(AF_INET, []):
        addr = d['addr']
        actual.append(addr)
    actual.sort()

    if not actual:
        print("no known addresses, giving up")
        return

    indns = []
    host = dns.name.from_text('%s.%s' % (name, zone))
    request = dns.message.make_query(host, dns.rdatatype.A)
    response = dns.query.tcp(request, nameserver)
    for entry in response.answer:
        for item in entry.items:
            indns.append(str(item))
    indns.sort()

    if actual == indns:
        if not force:
            return

        print("address not changed, updating anyway")

    else:
        print("IP address address for %s on %s.%s changed" % (
            interface, name, zone))

    print("actual: %s" % actual)
    print("in dns: %s" % indns)

    with open(keyfn) as f:
        key = f.readline().strip()

    keyring = dns.tsigkeyring.from_text({ zone + '.' : key })

    update = dns.update.Update(zone, keyring = keyring)
    update.replace(name, 300, 'A', actual[0])
    for a in actual[1:]:
        update.add(name, 300, 'A', a)

    response = dns.query.tcp(update, nameserver)

if __name__ == '__main__':
    main()
