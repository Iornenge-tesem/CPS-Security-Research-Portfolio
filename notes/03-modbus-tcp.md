# Modbus TCP: Frame Layout, Tank Mapping and Attacks

**Date:** 26 November 2026
**Roadmap item:** Phase 1, Section 3, Item 3 (Modbus TCP)

## Purpose
This note explains how Modbus TCP carries data between a PLC and a SCADA/HMI, maps my water tank onto Modbus objects, and shows how three attacks reach a plant through it. It sets up why my detector needs a physics model and cannot rely on Modbus values alone.

## How Modbus works
Modbus is a request and reply protocol. A **client** (the SCADA or HMI, formerly called the master) sends a request, and a **server** (the PLC, formerly the slave) answers. Modbus TCP carries these messages over ordinary networks, on **port 502**.

## The four data tables
A PLC exposes its data in four tables. Two hold single bits and two hold 16-bit numbers.

| Table | Holds | Client access | Tank example |
|---|---|---|---|
| Coils | 1 bit | read and write | pump ON/OFF command |
| Discrete inputs | 1 bit | read only | pump "running" feedback, a high-level switch |
| Input registers | 16-bit number | read only | the level reading |
| Holding registers | 16-bit number | read and write | the 1.5 m and 2.5 m thresholds |

- A **coil** is a command, and a **discrete input** is feedback on what actually happened. Comparing the two can reveal a problem.
- Registers hold whole numbers from 0 to 65535, so values are scaled. A level of 2.35 m is stored as 235 (hex `00 EB`).
- Addresses are numbered separately in each table. On the wire the first item is address 0. Some manuals use a different convention (for example, holding registers numbered from 40001), which is the same thing with a prefix and an offset of 1.
- The PLC program, not the register, makes decisions. A holding register only stores a number that the program reads.

## Function codes

| Code | Name | Table |
|---|---|---|
| 01 | Read coils | coils |
| 02 | Read discrete inputs | discrete inputs |
| 03 | Read holding registers | holding registers |
| 04 | Read input registers | input registers |
| 05 | Write single coil | coils |
| 06 | Write single register | holding registers |
| 15 (hex 0F) | Write multiple coils | coils |
| 16 (hex 10) | Write multiple registers | holding registers |

If a request fails, the server replies with the function code plus 0x80 (for example, 0x83 for a failed read of holding registers), followed by an exception code. Common exception codes are 01 illegal function, 02 illegal data address, 03 illegal data value and 04 server device failure.

## Frame layout
A Modbus TCP frame has a 7-byte header, then the function code and its data.

| Field | Size | Meaning |
|---|---|---|
| Transaction ID | 2 bytes | Label that matches a reply to its request |
| Protocol ID | 2 bytes | Always `00 00` for Modbus |
| Length | 2 bytes | Number of bytes that follow this field |
| Unit ID | 1 byte | Which device the message is for |

Multi-byte numbers are sent high byte first.

### Example: a write that turns the pump ON
`00 07 00 00 00 06 01 05 00 01 FF 00`

| Bytes | Field | Meaning |
|---|---|---|
| `00 07` | Transaction ID | request number 7 |
| `00 00` | Protocol ID | Modbus |
| `00 06` | Length | 6 bytes follow: unit (1) + function (1) + address (2) + value (2) |
| `01` | Unit ID | device 1 |
| `05` | Function code | write single coil |
| `00 01` | Address | coil 1, which is the pump in my tank |
| `FF 00` | Value | ON (`00 00` would be OFF) |

The PLC replies with an exact copy of the request. The matching transaction ID tells the client which request was answered.

### Example: a read of the level
Request `00 01 00 00 00 06 01 03 00 00 00 01` reads one holding register starting at address 0. A reply such as `00 01 00 00 00 05 01 03 02 00 EB` carries a byte count of 2 and the value `00 EB`, which is 235, or 2.35 m after undoing the scaling.

## My tank mapped to Modbus objects

| Tank item | Modbus table | Address | Type and scaling | Client can write? |
|---|---|---|---|---|
| Level reading | Input register | 0 | 16-bit, x100 (2.35 m is 235) | No |
| Pump command | Coil | 1 | 1 bit (written as `FF 00` for ON) | Yes |
| Pump status (is it really running) | Discrete input | 1 | 1 bit | No |
| Lower threshold (1.5 m) | Holding register | 0 | 16-bit, x100 (150, hex `00 96`) | Yes |
| Upper threshold (2.5 m) | Holding register | 1 | 16-bit, x100 (250, hex `00 FA`) | Yes |

## Three attacks through Modbus

| Attack | Function code | What the attacker sends | What the PLC does | What the operator sees | What a detector can check | ATT&CK |
|---|---|---|---|---|---|---|
| Unauthorized write to the pump coil | 05 | Write coil 1 = ON (the frame above) | Sets the coil and echoes the request. The pump stays on only if the program does not overwrite the coil on the next scan | Pump status shows ON, which is true, so command and status agree | Pump ON while the level is above 2.5 m or against the PLC's own logic, or a write from an unexpected source | Unauthorized Command Message (T0855, now under T1692.001) |
| Changed threshold register | 06 | Write holding register 1 = 350 (hex `01 5E`, 3.5 m) | Accepts it and keeps pumping up to 3.5 m | Nothing, unless the HMI reads that register (function 03) and shows it | A write outside the safe range (150 to 250), a write from a source that is not the engineering workstation, or the level passing the old limit | Modify Parameter (T0836) |
| Spoofed read response with a false level | 04 (the false value is in the reply) | A reply carrying a false level | If the lie is added on the network, the PLC still has the true level and runs correctly. If it is added at the sensor, the PLC is fooled too | A false but plausible level | Compare against the level predicted from the pump's history, and check how fast the reading changes | Spoof Reporting Message (T0856, now under T1692.002) |

Only someone in the path between the PLC and the SCADA, or at the sensor or PLC itself, can alter a reply. This is the network version of the sensor spoof I simulated in Item 2.

## Why Modbus is insecure
- It has **no authentication**: the PLC does not check who is asking.
- It has **no encryption**: anyone on the path can read the values.
- It has **no cryptographic integrity**: TCP's checksum catches accidents, not deliberate changes.
- The PLC obeys any valid frame from any device that can reach port 502.

A secure variant exists. The Modbus Organization publishes a Modbus Security protocol that wraps Modbus in TLS for authentication and integrity, on port 802. Plain Modbus TCP is still what most examples use.

## Where it sits on the Purdue Model
Modbus carries the traffic between Level 1 (the PLC) and Level 2 (the SCADA/HMI). An attacker who reaches that network, or who controls a Level 2 or Level 3 machine such as an engineering workstation, can send valid frames to the PLC.

## Link to my project
In my tank simulation, the sensor spoof lived at Level 0. Modbus is how a similar lie, or a forced command, can arrive over the network. Every attack above is a valid Modbus frame, so a check on the protocol alone sees nothing wrong. My detector has to judge the values against physics: the level predicted from the pump's history, limits on how fast the level can change, and safe ranges for the parameters.

## Open questions
- How can a detector tell a real operator write from a forged one when both are valid frames? Possible ideas: an allowlist of source addresses, range checks on written values, and the state of the process at the time.
- What does Modbus Security change? My guess is that it stops forged messages from outsiders but not a compromised authorized workstation or a spoof at the sensor. I have not checked this.
- If the PLC program rewrites the pump coil on every scan, how long does a forced write last?
- The frames in this note are decoded by hand. I have not yet compared them with a real packet capture.

## Sources
- Modbus Organization, specifications and implementation guides: https://modbus.org/modbus-specifications
- MITRE ATT&CK for ICS, Modify Parameter (T0836): https://attack.mitre.org/techniques/T0836/
- MITRE ATT&CK for ICS, Unauthorized Command Message (T0855): https://attack.mitre.org/techniques/T0855
- MITRE ATT&CK for ICS, Spoof Reporting Message (T0856): https://attack.mitre.org/techniques/T0856
- MITRE ATT&CK for ICS, Unauthorized Message (T1692): https://attack.mitre.org/techniques/T1692/001