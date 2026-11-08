# ICS Architecture of a Water Treatment Plant

**Date:** 8 November 2026
**Roadmap item:** Phase 1, Section 3, Item 1 (ICS architecture and the Purdue Model)

## Purpose
This note places the components of a water treatment plant on the Purdue Model and examines what an attacker could do at each level. It motivates physics-aware attack detection.

## The Purdue Model applied to a tank system

| Level | Components | Role | Talks to the level below via | Example attack | Type |
|---|---|---|---|---|---|
| 0 | Tank, level sensor, pump, valve | The physical process | (the process itself) | Spoofed sensor reading, so the PLC acts on false data | Cyber and physical |
| 1 | PLC / RTU | Reads inputs, runs control logic, drives outputs | Electrical signals or fieldbus wiring (e.g. 4-20 mA) | Unauthorized access to the PLC to change logic or outputs | Cyber |
| 2 | HMI, SCADA, engineering workstation* | Operator monitoring and commands, configuration of PLCs | Industrial protocols over Ethernet (e.g. Modbus TCP, DNP3) | HMI shows false data while the process goes wrong | Cyber |
| 3 | Historian, site operations | Records plant data over time | Standard network connections | Tampering with stored data, which can poison ML training data | Cyber |

*Diagrams place engineering workstations at Level 2 or 3. They program the PLCs, so compromising one is especially serious.

## Why OT security priorities differ from IT
IT prioritizes confidentiality first. OT prioritizes availability and safety first, then integrity, then confidentiality, because a shutdown or a false value can cause physical harm.

## Why a firewall is not enough
A firewall decides who may send traffic, not whether a command or reading is physically safe. A stolen credential, a compromised vendor laptop or an insider can send traffic that passes. Modbus has no authentication, so a PLC obeys what it receives. Sensor spoofing can also occur below the network layer. A reading must therefore be checked against the physics of the process.

## Link to my project
In my tank simulation, the sensor spoof happens at Level 0. The residual detector runs at Levels 2-3, so it only sees what lower levels report. It therefore needs its own physics model instead of trusting incoming data.

## Open questions
- How do real plants detect sensor tampering without a physics model?
- Where exactly should a detector sit so an attacker cannot also fool it?

## Sources
- NIST SP 800-82 Rev. 3
