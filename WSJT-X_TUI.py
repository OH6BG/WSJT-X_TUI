#!/usr/bin/env python3

"""

WSJT-X_TUI.PY - text-based UI to read spots from WSJT-X via the UDP port
(c) 2018 Jari Perkiömäki OH6BG

CHANGELOG:

29 Apr 2018: Initial release

Use WSJT-X v1.9.0 (rc versions ok), Python 3.6.x, and WSJTXClass by Randy K9VD
Download WSJT-X Python Class here: https://github.com/rstagers/WSJT-X/

"""

import socket
import time
import WSJTXClass

RX_CALL = 'N0CALL'
UDP_IP = "127.0.0.1"
UDP_PORT = 2237

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
basefreq = 0
mode_type = ''
DXList = []
start_time = time.time()

try:

    while True:

        fileContent, addr = sock.recvfrom(1024)
        NewPacket = WSJTXClass.WSJTX_Packet(fileContent, 0)
        NewPacket.Decode()

        if NewPacket.PacketType == 1:
            StatusPacket = WSJTXClass.WSJTX_Status(fileContent, NewPacket.index)
            StatusPacket.Decode()
            basefreq = StatusPacket.Frequency

        elif NewPacket.PacketType == 2:

            if not basefreq:
                continue

            DecodePacket = WSJTXClass.WSJTX_Decode(fileContent, NewPacket.index)
            DecodePacket.Decode()
            h = int(((DecodePacket.Time / (1000 * 60 * 60)) % 24))
            m = int(((DecodePacket.Time / (1000 * 60)) % 60))
            utc = '{:02}{:02}'.format(h, m)
            frequency = (int(basefreq) + int(DecodePacket.DeltaFrequency)) / 1000
            msg = DecodePacket.Message.split()

            if len(msg) > 2:
                if msg[0] == "CQ":  # "CQ OX6X KP03"
                    mode_type = "CQ"
                    if len(msg[1]) < 3:  # "CQ DX/EU/NA/AS OX6X"
                        dx = msg[2]
                    else:
                        dx = msg[1]
                else:
                    mode_type = "DE"
                    if len(msg[1]) > 2:
                        dx = msg[1]
                    else:
                        continue  # "73 DE OX6X"
            elif len(msg) == 2:
                if "/" in msg[0] or "/" in msg[1]:  # "SX3X OZ/OX6X" or "OZ/OX6X SX3X"
                    mode_type = "DE"
                    if len(msg[1]) > 2:  # "OX6X/QRP 73"
                        dx = msg[1]
                    else:
                        continue
                else:
                    continue
            else:
                continue

            # clear unique call list every 3 minutes
            if time.time() - start_time > 180:
                DXList = []
                start_time = time.time()

            # only allow unique calls to be spotted during the 3-minute period
            if dx not in DXList:
                DXList.append(dx)
            else:
                continue

            spot = "{} {:<10}{:8.1f}  {:<14} {:<5}{:3} dB  {:8}{:8}{:4}Z".format(
                "DX de",
                (RX_CALL + "-#")[:8] + ":",
                frequency,
                dx,
                "FT8",
                DecodePacket.snr,
                "",
                mode_type,
                utc,
            )

            print(spot)

            frequency = 0
            dx = ''
            mode_type = ''
            utc = ''

finally:
    sock.close()
