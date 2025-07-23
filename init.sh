#!/bin/bash

# IP virtuale e interfaccia (lo = loopback)
VIRTUAL_IP="10.10.255.254"
INTERFACE="lo"

# Check se l'IP è già assegnato
if ip addr show dev "$INTERFACE" | grep -q "$VIRTUAL_IP"; then
    echo " IP $VIRTUAL_IP già presente su $INTERFACE"
else
    echo " Aggiungo IP $VIRTUAL_IP a $INTERFACE..."
    sudo ip addr add "$VIRTUAL_IP/32" dev "$INTERFACE"
    echo "Fatto"
fi
