# picamera-webthing

A WebThing compatible Pi Camera server, for example to be used with the WebThingsIO Gateway.

## Screenshots (of the Gateway, `picamera-webthing` itself has no UI)

![Gateway with Pi Camera Thing added](/screenshots/gateway.jpg?raw=true "Gateway with Pi Camera Thing added")

## Features

* View still image camera snapshots @720p resolution
* View live 720p mjpeg camera stream @30fps
* Compatible with the WebThingsIO IoT Gateway v1.0.0 (see note above)
    * No special adapter required (just the generic `thing-url` adapter)
* Compatible with all Pi Camera modules that work with the Python `picamera` library

## Details

Uses the [`webthing-python`](https://github.com/webthingsio/webthing-python) library along with the `picamera` library.

## Pi Camera properties

Currently, no other camera property like frame rate, resolution, exposure, etc is 
exported as WebThing properties. This shall be added in later versions. 

### Still Image

The current still image is provided as a `ImageProperty`. The images are
JPEG encoded, which guarantees compatibility with the Gateway as well as any browser
used to display them.

### Live stream
The stream is provided as `VideoProperty`, encoded as MJPEG over HTTP. The latest Gateway version natively supports this,
as well as any other browser (too be fair I only tested it with Firefox).


