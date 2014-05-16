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

Command mode is intended to be reasonably human readable, data is transmitted as lines of arbitrary length (implementations should be able to flush to disk if necessary, a client configurable buffer size with a default of a megabyte or two is advisable) in UTF-8. Local systems can re-encode if needed, but all command mode operations must be in UTF-8. Case is significant, dammit. Lines are terminated by the linefeed character, Unicode code point 10 (decimal). Whitespace between the last non-whitespace character and the linefeed character must be disregarded as having no semantic meaning. This means you can transmit CRLF line ending if you really want, the protocol explicitly ignores the carriage return character.

Command mode lines form a **map**. A line consists of parenthesized key/value pairs. A key is a printable non-whitespace string within the standard ASCII range, followed by a space separating the key from the value, followed by the value which is an unstructured string terminated by a closing parenthesis. The formal grammar of a map is laid out below:

```
line  -> KVP+
KVP+  -> KVP | KVP NTEXT KVP+
KVP   -> "(" KEY <SPACE> VALUE ")"
NTEXT -> <ALL UNICODE CODEPOINTS>
KEY   -> <UNICODE CODEPOINTS 33-126 INCLUSIVE>
VALUE -> <ALL UNICODE CODEPOINTS>
```

To accommodate closing parentheses within value strings a closing parenthesis may be preceded by a backslash to indicate it is non-semantic. A double back slash signals non-escaping backslash. All value strings should be unescaped after being received. While no format is specified for value strings, some commands may specify specific string structures. Many of the core YASA commands will use this map format in a nested manner.

Any content occurring between map key/value pairs has no meaning and should be ignored. This space can be used for comments if you really want to add comments. For some reason. I guess.

Any line may contain an arbitrary number of key/value pairs however every command must contain at least an `ACTION` key which specifies the semantics for the rest of the keys in the command. Including keys not specified by the spec is not an error and is a valid mechanism for extension by third parties or for future versions of this specification.

### Transmission Mode

Transmission mode is used for transferring binary data. All transmission mode
transmissions start with the size of the data to be sent in bytes as a UTF-8
decimal string terminated either by the newline character or CLRF (clients must
accept both, a bare linefeed is preferred). The sender will then transmit the
data followed by the unencoded 16 byte MD5 digest of the data sent.

### Actions

- **HELO** Should be the first message sent in a session, HELO identifies the client in a session. Takes an additional mandatory key `I-AM` that contains a node reference identifying the sender.
- **OLEH** The only valid response to HELO. Identifiers the session server. Takes an additional mandatory key `I-AM` and non-mandatory `BUSY`. `I-AM` identifies the sender(the server) with a node reference. `BUSY`, if present, signals the server can not accept the session temporarily and that the client should retry shortly. `BUSY` may optionally contain a `REASON` key containing a human readable message and a `TIMEOUT` key specifying a suggested number of seconds to wait before attempting to initiate a new session. 

## Session Examples

There is no better way to clarify intent to implementors than to provide a rich set of examples. The following examples strive to conform to the spec above, but in cases of deviance where the spec is explicit, the spec is to be favored. If the spec has nothing to say or is ambitious, defer to the examples.

### Network Exploration
```
C: (ACTION HELO) (I-AM (UUID WORK@020AE080-DCB7-11E3-9C1A-0800200C9A66) (ADDR 198.69.124.70:7454) (VOL STABLE))
S: (ACTION OLEH) (I-AM (UUID HOME@8757BE80-DCB6-11E3-9C1A-0800200C9A66) (ADDR c-76-126-2-179.hsd1.ca.comcast.net:7454) (VOL VOLATILE))
```


