#!/bin/bash
curl http://localhost:5000/rockblock-incoming \
    -d imei=300234010753370 \
    -d momsn=12345 \
    -d "transmit_time=12-10-10 10:41:50" \
    -d iridium_latitude=52.3867 \
    -d iridium_longitude=0.2938 \
    -d iridium_cep=8 \
    -d data=48656c6c6f20576f726c6420526f636b424c4f434b
