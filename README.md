# YASA

Yet Another Synchronization Service, YASA, is a distributed file 
synchronization system which aims to reduce the pain of maintaing a large,
tagged, music collection across multiple machines and platforms. YASA is a
distributed system, so every machine (node) will have a full copy of the 
collection, will be able to manipulate said collection without restriction,
and no files will be stored on third party servers. If you want to maintain a
backup on a server, it's as simple as running a regular node there, but there
is it's not necessary to have server grade equipment to run a YASA network,
assuming you're not in a rush a YASA network can run exclusively on residential
connections with intermittent uptime for a theoretically unbounded number of 
nodes. While this repo contains the only present implementation, YASA is a
protocol as well as software. In addition to being the standard implementation,
this repo aims to house a reasonably well documented spec for the protocol
itself.

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

