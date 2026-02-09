#Measuring Camera Latency: A Personal Journal


Last week I was experimenting WebXR with webcam, it raised a interesting question for me: how good is the camera latency? After spending another weekend on the measurement I bring this blog, an incomplete journal on Camera Latency Measuring.


When talking about 'Latency', it's easily being mixed up with 'Frequency'. For example slogan of gaming monitor mention 'High Refresh Rate' brings you 'Low latency'. Let's consider a real-time football broadcast, your friend watches it on an 60HZ TV on earth, while you're watching on 1000HZ TV on the sun, then your eyes feels much smoother motion than your friend, while your latency is still worse since signal takes 8 minutes to arrive at 1000HZ TV. This example indicates that frequency only determine how small the time delta between two signal, and Latency means how long it takes the signal from real-world to the destination.

graph here

Before building up my own setup, I firstly tried a [script from github](https://github.com/perrytsao/Webcam-Latency-Measurement)

graph here

the logic is straightforward:

while read camera image
  draw timestamp on camera image
  show this image on screen

Then point camera to the gui window, create two "reflections" in streaming, then you see 
two timestamp in streaming, older one is previous round image shown on screen, newer one
is when such capture (of previous image) arrived to application, difference should be the latency
from camera to application.

when I tried this script with my webcam (30FPS), I got 32 milliseconds and 36 milliseconds,
and what interested me is the script also output FPS of captured image, shows 27.x FPS or 31.x FPS
seems... Perfectly match the latency 32 x 31 ~ 1000  and 36 x 28 ~ 1000, is this by accident?
Let's drawing a diagram to see how different blocks connected together:

graph

Let's draw in it in another way, camera image originated: this should give you better understanding:
The two timestamps appeared on one image, is always the timestamp we mark in the loop, so of course
the delta between two timestamp is just the interval between two camera image! The issue is that 
the timestamp which used as measure start is bounded to camera frequency (because the script draw on
camera image and show it), even the camera latency is faster, the start timestamp is already out-of-date,
so the measured latency is also bounded to the image interval.

Inspired by the script, we should decouple the startup timestamp mark frequency from camera frequency,
as fast as possible. My monitor working at 165HZ, much higher than webcam (30), should be good enough for this task.

First Try:

   Using console text print, it works like this:
  
gif

  Result: failed, flushing too fast, camera can't catch clear text at all

Second Try:

  Spread the timestamp text along whole line, so individual timestamp will stay stable for a while.  Result: failed, still too fast


This approach also have other issues:
* flushing doesn't aligned to V-sync
* the code is running under virtual terminal, terminal might have it's internal buffering which lead extra latency
* virtual terminal is also controlled by window manager, which might also introduce extra latency
* I have to manually look into every image to get result, can't automatic

The core idea is to draw 

* Linux KMS/DRM API, allow you to control 




Then I made some changes to that script, replace text timestamp with QRCode, also record the delta
(since last time capture) into file, 

















Nvidia measure input E2E latency? it's called (LDAT)[https://developer.nvidia.com/nvidia-latency-display-analysis-tool], a photon sensor attached in front of monitor, and registered as mouse. It measure the elapsed time
after emulated mouse click up to corresponding flush on monitor, This Digital Foundry Video shows how it works:

https://www.youtube.com/watch?v=TuVAMvbFCW4  at 3:21


