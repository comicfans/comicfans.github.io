#Measuring Camera Latency: A Personal Journal


Last week I was experimenting WebXR with webcam, it raised a interesting question for me: how good is the camera latency? After spending another weekend on the measurement I bring this blog, an incomplete journal on Camera Latency Measuring.


When talking about 'Latency', it's easily being mixed up with 'Frequency'. For example slogan of gaming monitor mention 'High Refresh Rate' brings you 'Low latency'. Let's consider a real-time football broadcast, your friend watches it on an 60HZ TV on earth, while you're watching on 1000HZ TV on the sun, then your eyes feels much smoother motion than your friend, while your latency is still worse since signal takes 8 minutes to arrive at 1000HZ TV. This example indicates that frequency only determine how small the time delta between two signal, and Latency means how long it takes the signal from real-world to the destination. That's also the reason 
TV having 'gaming' mode to turn off time consuming image enhancing algorithm. Refresh rate stay the same, but latency from digital input to physical output will be lower.

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/tv_example.png)

Before building up my own setup, I firstly tried a [script from github](https://github.com/perrytsao/Webcam-Latency-Measurement)

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/original_webcam.png)

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
the delta between two timestamp is just the interval  between two (or more) camera image! The issue is that 
the timestamp which used as measure start is bounded to camera frequency (because the script draw on
camera image and show it), even the camera latency is lower than that interval, the marked start time 
is already out-of-date (since no camera update during that period), the measured latency precision is 
also bounded to the image interval. 

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
* under GUI virtual terminal, might have it's internal buffering which lead extra latency
* GUI output controlled by window manager, hard to reason about buffer queue.
* Manually look into every image required, not automatic

Firstly I tried to put Linux running under VGA/SVGA mode (to get ride of KMS/DRM stack),
but after some rounds searching with chatgpt/google, I found such functionality
already implemented by graphics card (instead of monitor), and on UEFI this is replaced by GOP,
No support for high refresh rate other than 60HZ is also a major problem. Then I looked into
KMS/DRM information, it already support what I need

* complete frame buffer control, no window system/manager in charge.
* atomic flip, allow perfect match to V-sync
* support OpenGL(ES) painting, GPU still take the heavy lifting
 
And then I find a library [SRM](https://cuarzosoftware.github.io/SRM/index.html) which is a thin wrapper of KMS/DRM
allow you quickly start OpenGL(ES) drawing. This time I use QRcode to display timestamp information
on screen, so automatic post-processing can be applied. Similar to the text painting, the painting
also arrange QrCode on different area of screen and stay for a while, 
with this trick, even monitor is flushing at 165 HZ, one QRCode can stay for more than 1/165 second,
the more you arrange, the longer it stay, so even 30 FPS camera can also have enough time to capture stable image.
Without this, a QRCode may already show on screen and then disappeared without camera notice.
DRM/KMS also provides notify callback when flip is finished, allow us to record the timing information.


for KMS/DRM opengl painting (with SRM), it works like this way:

* you receive page flipped notification, knows that previous frame buffer already
being flipped, record timing information.
* paintGL callback will only trigger once before next frame flip, so you can draw anything for next frame, 
   then using srmConnectorRepaint. such frame buffer will be used for next flip
* since there's no way to measure the time spend on page flip itself (after we sending flip to kernel, up to the monitor start sending photon for that contents). the best we can do is to use the page flipped (of previous time) timestamp, and assume time that contents start displaying on monitor shouldn't be later than next flip (I don't have super long DP/HDMI cable, neither my monitor support image enhancing).



By recording these timing, I got following plot:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/page-flipped-timing.png)

FPS caluclated from this timing is 165.0786808021504

the monitor information reported by xrandr
```
  2560x1440 (0x1c2) 645.000MHz +HSync -VSync *current +preferred
        h: width  2560 start 2568 end 2600 total 2640 skew    0 clock 244.32KHz
        v: height 1440 start 1446 end 1454 total 1480           clock 165.08Hz

```
the FPS should be 645000000 / 2640 / 1480 ~ 165.07985 FPS

differences < 1e-5, should be good enough

I also use my phone's 240FPS slow motion to verify such setup actually work

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/phone-slow-motion.gif)

and then run a python script to compare the timestamp. The slowmo video information
```
ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate,r_frame_rate -of default=noprint_wrappers=1 slowmo_clock_boottime.MOV


r_frame_rate=240/1
avg_frame_rate=154080/641 ~ 240.37 FPS
```

the trick here is to use avg_frame_rate (actual file frame rate) instead of r_frame_rate. Consumer grade slow motion recording 
usually deployed variable frame rate, 240 is not always the exactly value. then compare the delta between slowmo frame timestamp
and the latest QrCode timestamp on that frame (by aligning first slowmo frame time to first frame latest Qrcode timestamp).
we got following result:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/slow-motion-page-flip-diff.png), 

Here we see the jitter between two timestamp, since monitor refresh timing doesn't aligned to slowmo capture timing, it's possible
that for one monitor fresh, the phone just capture latest content, but for another fresh, that timestamp already shown for 6 ms and
being captured by phone

combined with the slow motion video (no more than one new image appear at same time), now I'am confident to say the 
KMS/DRM Qrcode display code is working as expected. Now using my
webcam for similar analysis:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/my_latency_30fps.png), 




this plot makes more sense. The best case latency is 32ms, Note, we're using previous frame page flipped
callback time as the QrCode, and mark the received back time of the camera(which including the page flipped timestamp),
so it's already a closed cycle, all possible latency already considered (including the time spend on signal travel the cable and became photon from monitor)
so this is the "worst case of" best case value. "best case of" best case latency can be 32ms - 1/165.07868 sec ~ 26ms, 
(if the duration starts when page flipped up to next frame being on display is exactly 1 monitor frame time)
and due to monitor flush rate not aligned to webcam shutter, it's possible that shutter just missed the new monitor contents, then that contents
being captured by next shutter, which is the worst case (51.5 ms). In theory the worst case latency should be equal to best case latency + 1 webcam frame time (33ms)
here we have delta between best and worst case being 19.5 ms, because the camera shutter is not instant, it needs to work earlier before next frame transfer.
the average latency (worst case) is 41.1853.


Now let's verify the latency for low FPS setup. By forcing the FPS to 10, we can observe the differences between my measure and original script.
we can predict that original script bound the update frequency to camera frequency, so it won't gives latency that lower than 1/10 sec.
I also made some changes to that script, painting qrcode instead of text timestamp, also recording the elapsed time since last time received image
first, let's see the elapsed time (delta between two capture)

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/10fps_capture_delta.png), 

the fps is a little offset to 10, actually it's 8.9 FPS most of time, and if we compare the delta between previous capture 
and the delta between two timestamp on image (by qrcode), we will see
 
```
delta to prev capture, delta of two timestamp on image
 0.1120000000000001,  0.112,
 0.11600000000000055, 0.116,
 0.1120000000000001,  0.112,
 0.11199999999999921, 0.112,
 0.11600000000000055, 0.116,

 ...
 0.11200000000000188, 0.112,
 0.11199999999999832, 0.112,
 0.11599999999999966, 0.116,
 0.11200000000000188, 0.112,
 0.11199999999999832, 0.112,
 0.11600000000000321, 0.116,
 0.11199999999999832, 0.112,
 0.11199999999999832, 0.112

```

this clearly shows that the 'latency' original script measure, is essential the delta between two capture,
not the time signal travel to application. It's easy understandable if we consider a camera that only takes
1 picture every 1 hour, the latency that camera send picture to application, won't be as slow as an hour,
but due to the text drawn on image only update once per hour, so delta between text is always an hour.
so original script result is only meaningful when transfer latency is much longer than one interval period.
(original script also link to a result table of some camera tested, shows that the latency are always greater than one interval)

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/original_tests.png)

since I run original script with 30FPS setup and always got exactly 1 interval delta, it prove that the latency
should be always less than one interval. Note, this conclusion doesn't conflict with previous 51.5 worst case result,
the latency actually came from three parts:

1. the time spend on signal travel over usb to our application memory, which is the fixed part
2. the time camera wait from previous shutter complete, up to next shutter starts, which is FPS dependent
3. the time when latest timestamp is flushing on screen. For 165HZ monitor, even we flush at every V-sync, one fixed timestamp will stay on screen for about 6 milliseconds, which also add latency, just like the time differences we use 240 slowmo to capture 165 monitor image.

for reason 2 and 3, we can still have worst case latency that longer than one interval, but the captured timestamp delta perfectly
matching interval, it can prove that before camera capture next frame, the exactly previous frame already being captured and shown on display, so in-between frames pending in queue,
(otherwise two timestamps in one image must have delta >= 2*interval , not exactly equals to 1 interval)


now let's measure it with my approach, this time it's more tricky, since the camera doesn't work the exactly
way at different FPS, for 30 FPS streaming, even camera can't capture every monitor update, every frame still
shows the correct pattern of image: clearest image always appear at bottom right (because we update qrcode top-bottom, left-right)
but 10FPS is like this:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/10fps_9_qrcode.gif), 

no clear image pattern. looks like all qrcode appear/disappear at same time, lead lots of empty image. 
my suspection is the shutter time too long, the short appear time image signal will be 'smooth' out.
so I increase the number of qrcode grid from 3x3 to 4x4, also increasing the stay time of every qrcode,
then the capture like this

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/10fps_16_qrcode.gif), 

and the latency plot

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/10fps_latency_plot.png), 

average latency 82.9 ms, best case 53 ms, worst case 113 ms


How Nvidia measure input E2E latency? it's called (LDAT)[https://developer.nvidia.com/nvidia-latency-display-analysis-tool], a photon sensor attached in front of monitor, and registered as mouse. It measure the elapsed time
after emulated mouse click up to corresponding flush on monitor, This Digital Foundry Video shows how it works:

https://www.youtube.com/watch?v=TuVAMvbFCW4  at 3:21


