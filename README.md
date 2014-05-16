# YASA

Yet Another Synchronization Application, YASA, is a distributed file synchronization system which aims to reduce the pain of maintaing a large, tagged, music collection across multiple machines and platforms. YASA is a distributed system, so every machine (node) will have a full copy of the collection, will be able to manipulate said collection without restriction, and no files will be stored on third party servers. If you want to maintain a backup on a server, it's as simple as running a regular node there, but there is it's not necessary to have server grade equipment to run a YASA network, assuming you're not in a rush a YASA network can run exclusively on residential connections with intermittent uptime for a theoretically unbounded number of nodes. While this repo contains the only present implementation, YASA is a protocol as well as software. In addition to being the standard implementation, this repo aims to house a reasonably well documented spec for the protocol itself.

## Terminology
A **Node** represents a subset of a complete complete library. Presently YASA does not support any sharding strategy, so every node is a complete copy (still a subset, btw) of the total library. Sharding will likely appear in future revisions of the protocol. Typically a node will represent a single machiene, but multiple nodes on the same computer, or a single node shared locally via a network drive are both possible as well.

A **Node Reference** uniquely identifies a node. One consists of

- a UUID identifying a node
- a host/port pair (DNS and IP addresses are valid)
- an address stability status (see below)

UUIDs should persist for the lifetime of a node while addresses may change over time.

A **Network** consists of an undirected graph of connected nodes which together represent a complete library. In a stable state a network should be _complete_, that is every node should have a node reference pointing to every other node in the network.

Every node is either considered **address stable** or **address volatile**. These properties can be thought of as describing the machine as having a static or dynamic IP address. They allow for more efficient location of nodes which are down or have changed address. Every node decides its own stability status and all other nodes must respect it. A simple implementation may opt to consider every node as address volatile at some (generally minor) performance cost.

## Protocol

The YASA protocol has two modes, command and transmission. 

### Command Mode
Command mode is intended to be reasonably human readable, data is transmitted 
as lines of arbitrary length (implementations should be able to accept lines 
of at least 1000 bytes, preferably more contingent on system resources) in 
UTF-8. Local systems can re-encode if needed, but all command mode operations 
must be in UTF-8. Lines are terminated by the linefeed character, Unicode code
point 10 (decimal). Whitespace between the last non-whitespace character and
the linefeed character must be disregarded as having no semantic meaning. This
means you can transmit CRLF line ending if you really want, the protocol 
explicitly ignores the carriage return character.

### Transmission Mode
Transmission mode is used for transferring binary data. All transmission mode
transmissions start with the size of the data to be sent in bytes as a UTF-8
decimal string terminated either by the newline character or CLRF (clients must
accept both, a bare linefeed is preferred). The sender will then transmit the
data followed by the unencoded 16 byte MD5 digest of the data sent.

