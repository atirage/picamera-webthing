# -*- coding: utf-8 -*-

#!/usr/bin/env python3

from webthing import (Action, Event, Property, Value, SingleThing, Thing, WebThingServer)
import picamera
import threading
import time
import syslog
import tornado.web
import io
from asyncio import sleep, Event, get_event_loop

PATH_JPG = '/media/screenshots/snapshot.jpg'

class StreamHandler(tornado.web.RequestHandler):
    async def get(self):
        #self.set_header('Cache-Control', 'no-store', no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        #self.set_header('Pragma', 'no-cache')
        #self.set_header('Connection', 'close')
        self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
        await self.flush()
        my_boundary = "--jpgboundary\r\n"
        while True:
            # Generating images for mjpeg stream and wraps them into http resp
            await new_frame.wait()
            new_frame.clear()
            with io.open(PATH_JPG, 'rb') as f:
                img = f.read()
            self.write(my_boundary)
            self.flush()
            self.set_header('Content-type', 'image/jpeg')
            self.set_header('Content-length', str(len(img)))
            self.write("\r\n")
            self.write(img)
            self.write("\r\n\r\n")
            self.served_image_timestamp = time.time()
            try:
                await self.flush()
                #print(self.served_image_timestamp)
            except tornado.iostream.StreamClosedError as err:
                #print(err.real_error)
                break

class SnapshotHandler(tornado.web.RequestHandler):
    async def get(self):
        self.set_header('Content-type', 'image/jpeg')
        await new_frame.wait()
        new_frame.clear()
        with io.open(PATH_JPG, 'rb') as f:
            img = f.read()
        self.set_header('Content-length', str(len(img)))
        self.write(img)
        self.served_image_timestamp = time.time()
        try:
            await self.flush()
            #print(self.served_image_timestamp)
        except tornado.iostream.StreamClosedError as err:
            #print(err.real_error)
            pass

class StreamOutput(object):
    def __init__(self):
        self.snapshot = None

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # Start of new frame, reopen
            self.snapshot = io.open(PATH_JPG, 'wb')
        self.snapshot.write(buf)
        if buf.endswith(b'\xff\xd9'):
            #self.snapshot.close()
            _loop.call_soon_threadsafe(new_frame.set)
            
    def close(self):
        self.snapshot.close()

class PiCameraThing(Thing):
    """A web connected Pi Camera"""
    def __init__(self):
        Thing.__init__(self,
                       'urn:dev:ops:my-picam-thing-1234',
                       'My PiCamera Thing',
                       ['VideoCamera'],
                       'A web connected Pi Camera')
        self.terminated = False
        self.picam = picamera.PiCamera(resolution='720p', framerate=30)
        self.still_img = Value(None)
        self.add_property(
            Property(self, 'snapshot', self.still_img,
                    metadata = {
                                '@type': 'ImageProperty',
                                'title': 'Snapshot',
                                'type': 'null',
                                'readOnly': True,
                                'links': [
                                         {
                                            'rel': 'alternate',
                                            'href': '/media/snapshot',
                                            'mediaType': 'image/jpeg'
                                         }
                                         ]
                                }))
        #self.stream_active = Value(False)
        #self.add_property(
        #    Property(self, 'streamActive', self.stream_active,
        #            metadata = {
        #                        'title': 'Streaming',
        #                        'type': 'boolean',
        #                        }))
        self.stream = Value(None)
        self.add_property(
            Property(self, 'stream', self.stream,
                metadata = {
                            '@type': 'VideoProperty',
                            'title': 'Stream',
                            'type' : 'null',
                            'readOnly': True,
                            'links': [
                                     {
                                        'rel': 'alternate',
                                        'href': '/media/stream',
                                        'mediaType': 'video/x-jpeg'
                                     }
                                     ]
                            }))
        syslog.syslog('Starting the camera')
        self.cam_thr = threading.Thread(target=self.start_PiCam, args=())
        self.cam_thr.start()
    
    def start_PiCam(self):
        try:
            self.picam.start_preview()
            # Give the camera some warm-up time
            time.sleep(2)
            output = StreamOutput()
            self.picam.start_recording(output, format='mjpeg')
        except:    
           syslog.syslog('Error setting up recording!')
        while not self.terminated:
            self.picam.wait_recording(2)
        self.picam.stop_recording()
        output.close()

global _loop, new_frame

if __name__ == '__main__':
    
    _loop = get_event_loop()
    new_frame = Event()

    picamera_web_thing = PiCameraThing()
    server = WebThingServer(SingleThing(picamera_web_thing), 
                            port=8900, 
                            additional_routes=[ (   
                                                    r'/media/stream', 
                                                    StreamHandler
                                                ),
                                                (
                                                    r'/media/snapshot',
                                                    SnapshotHandler
                                                )])
    try:
        syslog.syslog('Starting the Webthing server on: ' + str(server.hosts))
        server.start()
    except KeyboardInterrupt:
        picamera_web_thing.terminated = True
        picamera_web_thing.cam_thr.join()
    finally:
        pass
