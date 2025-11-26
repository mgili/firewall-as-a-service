# Firewall-as-a-Service

This project implements an Intrusion Detection System (IDS) based on Suricata, featuring dynamic blacklisting capabilities and real-time threat mitigation. The system is designed to detect malicious network activities, specifically port scanning attacks, and automatically block malicious IP addresses using iptables firewall rules.

The core goal is to automate threat mitigation by developing a system that responds to detected threats by dynamically blacklisting malicious IP addresses. Real-time synchronization is achieved through a WebSocket-based communication channel that ensures instant blacklist updates across all system components.

---

## Project Architecture

The project consists of :
- the Suricata Server, which acts as the intrusion detection engine analyzing all network traffic
- the web server hosts the protected web service and is responsible for capturing traffic and enforcing security policies
- two traffic simulators generate different types of network activity: the Normal Traffic Simulator produces legitimate HTTP requests, while the Port Scanner Simulator generates malicious port scanning traffic

```
┌─────────────────┐         
│ Normal Traffic  │         ┌───────────────────────────────────┐
│ Simulator (curl)│────────▶│            Web Server             │
└─────────────────┘         │  - Apache Web Server (80)         │
                            │  - Traffic Capture (tcpdump)      │
┌─────────────────┐         │  - WebSocket Manager Daemon       │
│ Port Scanner    │────────▶│  - iptables Blacklist Management  │
│ Simulator (nmap)│         └───────────────────────────────────┘
└─────────────────┘                   │                ▲
                      Traffic Stream  │                |  WebSocket
                                      ▼                ▼
                          ┌──────────────────────────────────────┐
                          │         Suricata Server              │
                          │  - Network Traffic Analysis (9191)   │
                          │  - Blacklist Daemon                  │
                          │  - WebSocket Server (9192)           │
                          └──────────────────────────────────────┘
```

The communication flow begins with the traffic simulators sending requests to the web server, simulating both normal user activity and malicious scanning attempts. The endpoint captures all incoming network traffic using tcpdump and streams it to the Suricata Server via netcat. Suricata continuously analyzes this traffic stream using predefined detection rules to identify suspicious patterns, particularly port scanning activities.

When Suricata detects malicious behavior and triggers an alert, the Blacklist Daemon immediately adds the source IP address to the blacklist database. The WebSocket Server, which monitors the blacklist file for changes, instantly broadcasts these updates to all connected clients. The endpoint's WebSocket Manager Daemon maintains a persistent connection to receive these blacklist notifications and immediately configures iptables firewall rules to block traffic from the malicious IP addresses, completing the automated threat response cycle.

---

## Technical Implementation

The system's detection capabilities rely on Suricata rules that identify malicious network activities. The primary detection rule monitors for TCP SYN packets, which are used in the initial handshake of a TCP connection. When the same source IP address sends five or more SYN packets to different ports within a sixty-second window, it indicates a likely port scan attempt, triggering an alert. A complementary rule detects TCP NULL scans, a stealthier scanning technique where packets are sent with no TCP flags set. This rule triggers when three or more such packets are observed from the same source within thirty seconds. A third rule protects the system from HTTP flood denial-of-service attacks. This rule identifies when a single source IP sends twenty or more HTTP requests within a ten-second window, which indicates a potential HTTP flooding attack. The threshold-based approach prevents alert flooding by aggregating similar events while maintaining high detection accuracy across all attack types.

The traffic capture and analysis pipeline forms the backbone of the system's monitoring capabilities. On the endpoint, tcpdump continuously captures all inbound network traffic with unbuffered output to ensure real-time processing. This packet data is written to stdout and immediately piped through netcat to the Suricata server listening on port 9191. On the Suricata side, a named pipe receives the incoming traffic stream from netcat, allowing Suricata to process the packets in real-time as if reading from a live network interface. This architecture enables centralized traffic analysis while keeping the detection logic isolated from the protected endpoint.

### Blacklist Management

The blacklist system operates through three coordinated components. On the Suricata server, the Blacklist Daemon continuously monitors the alert log file using a file system watchdog mechanism. Whenever Suricata generates an alert, the daemon immediately reads the event, extracts the source IP address, and adds it to an in-memory set of blacklisted addresses. This blacklist is then persisted to a JSON file with timestamp information, creating a permanent record of all identified threats.

The WebSocket Server runs alongside the Blacklist Daemon on the Suricata server. It uses the same file watchdog pattern to monitor the blacklist JSON file for any changes. When the blacklist is updated, the server immediately broadcasts a notification message to all connected WebSocket clients. This asynchronous communication pattern ensures that blacklist updates are propagated in real-time.

On the endpoint side, the Blacklist Manager acts as a WebSocket client, maintaining a persistent connection to the Suricata server. It listens continuously for blacklist update messages and, upon receiving them, immediately translates the IP addresses into iptables firewall rules. For each blacklisted IP, it inserts a DROP rule at the beginning of the INPUT chain, ensuring that all traffic from that address is blocked at the network level.