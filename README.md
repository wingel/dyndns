dyndns updater
==============

A small script for sending dynamic DNS updates to a bind 9 server

I've tested this on a Linux Mint 17 machine.  Everything should work
the same on Ubuntu 14.04.  If you are running a RedHat derivative
you'll have to figure out how to install the prequisites yourself.

Creating a key
==============

Install the following packages:

    apt-get install bind9utils

Create a key with:

    dnssec-keygen -a hmac-md5 -b 512 -n host dyndns.example.com

This will generate two files (the numbers will differ):

    Kdyndns.example.com.123+45678.key
    Kdyndns.example.com.123+45678.private

Find the key in the generated K.private file (the key is a lot longer
but I've shortened it to make this easier to read):

    Key: jQn+dztU/Yi2xuST/...gbgbCHe5Y2HEljlvNaQ==

Remember this key for later.

DNS server configuration
========================

Prerequisites:

You need a subdomain that you can use and which points at the machine
where you are going to run bind.  I'm not going to tell you how to do
that.

Install the nameserver, bind version 9:

    apt-get install bind9

Create a directory where you will put the zone files.  This directory
must be writable by the bind user:

    mkdir /etc/bind/dyndns
    chown bind.bind /etc/bind/dyndns
    chmod 755 /etc/bind/dyndns

In that directory, create a new zone file, for exampe
/etc/bind/dyndns/dyndns.example.com.zone with the following contents:

    $ORIGIN .
    dyndns.example.com      IN SOA  root.example.com. root.localhost. (
				    2014070109 ; serial
				    10800      ; refresh (3 hours)
				    900        ; retry (15 minutes)
				    604800     ; expire (1 week)
				    86400      ; minimum (1 day)
				    )
			    NS      ns.example.com.
    $ORIGIN dyndns.example.com.

Fix the owner and permissions on the zone file:

    chown bind.bind /etc/bind/dyndns/dyndns.example.com.zone
    chmod 644 /etc/bind/dyndns/dyndns.example.com.zone

Create a file for example /etc/bind/named.conf.keys, where you will
store the key and make sure it's only writeable by root and only
readable by the bind user:

    touch /etc/bind/named.conf.keys
    chown root.bind /etc/bind/named.conf.keys
    chmod 640 /etc/bind/named.conf.keys

Edit the file to have the following contents, the key material is from
the K.private file above:

    key "dyndns.example.com" {
        algorithm hmac-md5;
        secret "jQn+dztU/Yi2xuST/...gbgbCHe5Y2HEljlvNaQ==";
    };

Add the following to your /etc/bind/named.conf.local:

    include "/etc/bind/named.conf.keys";

    zone "dyndns.example.com" {
        type master;
        file "/etc/bind/dyndns/dyndns.example.com.zone";
        allow-update { key "dyndns.example.com"; };
    };

The "allow-update" statement tells it that a client which knows the
key is allowed to update the zone.

Reload the DNS server configuration:

    service bind9 reload

The server side is now ready.

Client configuration
====================

Install the following packages on the client which wants to send
dynamic DNS updates to the server:

    apt-get install python-netifaces python-dnspython

Create a directory where you store the DNS update key and make sure
only you have access to that directory:

    mkdir ~/keys
    chmod 700 ~/keys


Put the key material from the K.private file above into a file in the
directory:

    echo "jQn+dztU/Yi2xuST/...gbgbCHe5Y2HEljlvNaQ==" >~/keys/dyndns.example.com

The client side is now ready.

Periodically run the update-dyndns script to check the DNS
information and update it if it has changed.  The syntax is:

    ./update-dyndns.py nameserver zone hostname interface key-file

for example, to ask the nameserver ns.example.com to update
grumpy.dyndns.example.com with the IP addresses from eth0, do:

    ./update-dyndns.py ns.example.com dyndns.example.com grumpy eth0 ~/keys/dyndns.example.com

or use cron to do it every minute.  Edit your crontab with:

    crontab -e

and add a line like this:

    * * * * * $HOME/bin/update-dyndns.py ns.example.com dyndns.example.com grumpy eth0 $HOME/keys/dyndns.example.com

