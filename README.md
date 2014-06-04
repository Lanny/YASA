# YASA

Yet Another Synchronization Application, YASA, is a set of utilities for maintaining synchronized, large, and expanding music collections across multiple computers. YASA employees a pretty straightforward server/client design where the server and every client have a full copy of the library. Every client can read and write to the server. The synchronization and conflict resolution algorithms are truly primitive, the value proposition of YASA is that it can divine the appropriate synchronization action based on normal iTunes interaction. If you delete a file on one computer, that deletion will be propagated to every other computer running the YASA client.

The YASA client utilities target an up-to-date version of iTunes on the platforms which iTunes supports (OSX and Windows). YASA uses the platform standard APIs, so backwards compatibility should be reasonable but I make no promises. The server component should run on anything with a 2.5+ python interpreter.

## Protocol

Here are some notes about how the YASA components talk to each other. Most of it is probably wrong and you should definitely defer to the code if there's a discrepancy.

### Modes

The YASA protocol has two modes, command and transmission. 

#### Command Mode

Command mode is intended to be reasonably human readable, data is transmitted as lines of arbitrary length (implementations should be able to flush to disk if necessary, a client configurable buffer size with a default of a few dozen kilobytes is advisable) in UTF-8. Local systems can re-encode if needed, but all command mode operations must be in UTF-8. Lines are terminated by the linefeed character, Unicode code point 10 (decimal). Whitespace between the last non-whitespace character and the linefeed character must be disregarded as having no semantic meaning. This means you can transmit CRLF line endings if you really want, the protocol explicitly ignores the carriage return character.

All commands are **maps** (see below) with at least an `ACTION` key which specifies the semantics for the rest of the keys in the command. Including keys not specified by the spec is not an error and is a valid mechanism for extension by third parties or for future versions of this specification.

#### Transmission Mode

Transmission mode is used for transferring binary data. All transmission mode
transmissions start with the size of the data to be sent in bytes as a UTF-8
decimal string terminated either by the newline character or CLRF (clients must
accept both, a bare linefeed is preferred). The sender will then transmit the
data followed by the unencoded 16 byte MD5 digest of the data sent.

### Data Structures

#### Strings
String means "UTF-8 encoded string" and nothing else ever.

#### Maps
Maps are key/value pairs. A map consists of parenthesized key/value pairs. A key is a printable non-whitespace string within the standard ASCII range, followed by a space separating the key from the value, followed by the value which is an unstructured string terminated by a closing parenthesis. The formal grammar of a map is laid out below:

```
line  -> KVP+
KVP+  -> KVP | KVP NTEXT KVP+
KVP   -> "(" KEY <SPACE> VALUE ")"
NTEXT -> <ALL UNICODE CODEPOINTS>
KEY   -> <UNICODE CODEPOINTS 33-39 AND 42-126 INCLUSIVE>
VALUE -> <ALL UNICODE CODEPOINTS>
```

To accommodate closing parentheses within value strings a closing parenthesis may be preceded by a backslash to indicate it is non-semantic. A double back slash signals a non-escaping backslash. All value strings should be unescaped after being received. While no format is specified for value strings, context will dictate what subset of well formed values is considered meaningful. Since values are simply strings, you'll see nested maps in many core YASA components.

Any content occurring between map key/value pairs has no meaning and should be ignored. This space can be used for comments if you really want to add comments. For some reason. I guess. Please don't add comments though.

#### Lists
Lists are a special case of maps which describe sequential data (everyone loves JS, right?). They contain a `LENGTH` key who's value is the decimal number of items in the list. All other meaningful keys are integer numbers from 0 to the value of the `LENGTH` key, left inclusive. To be well formed a list must enumerate every index from 0 to the list length, even if the value corresponding to the index is the empty string.

### Actions

**This is totally out of date and needs to be rewritten. Ignore it**

You may notice a theme.

- **HELO** [client] Should be the first message sent in a session, HELO identifies the client in a session. Takes an additional mandatory key `I-AM` that contains a node reference identifying the sender.
- **OLEH** [server] The only valid response to HELO. Identifiers the session server. Takes an additional mandatory key `I-AM` and non-mandatory `BUSY`. `I-AM` identifies the sender(the server) with a node reference. `BUSY`, if present, signals the server can not accept the session temporarily and that the client should retry shortly. `BUSY` may optionally contain a `REASON` key containing a human readable message and a `TIMEOUT` key specifying a suggested number of seconds to wait before attempting to initiate a new session.
- **LIST-HASHES** [client] A request for the server to send the hash of every file its tracking. No additional keys
- **SEHSAH-TSIL** [server] Response to LIST-HASHES. One additional key, `HASHES`, is a list of hexadecimal encoded md5 identity hashes of every file being tracked.
- **SHARE-NODES** [client] A request for all nodes considered by the server to be part of the network (what exactly that means is a network policy). No additional keys are defined.
- **SEDON-ERAHS** [server] Response to SHARE-NODES. One key is defined, `REFS`, which is a list of node references which the server recognizes as part of the network. Should not include the client's node reference.
- **NET-POLICY** [client] A request for all network the network policies.
- **YCILOP-TEN** [server] Response to NET-POLICY. Single mandatory additional key `POLICY` is a map of policy names to values.
