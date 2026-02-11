#Measuring Camera Latency: A Personal Journal


Last week I was experimenting WebXR with webcam, it raised a interesting question for me: how good is the camera latency? After spending another weekend on the measurement I bring this blog, an incomplete journal on Camera Latency Measuring.


When talking about 'Latency', it's easily being mixed up with 'Frequency'. For example slogan of gaming monitor mention 'High Refresh Rate' brings you 'Low latency'. Let's consider a real-time football broadcast, your friend watches it on an 60HZ TV on earth, while you're watching on 1000HZ TV on the sun, then your eyes feels much smoother motion than your friend, while your latency is still worse since signal takes 8 minutes to arrive at 1000HZ TV. 

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/tv_example.png)

This example indicates that frequency only determine how small the time delta between two signal, and Latency means how long it takes the signal from real-world to the destination. It's also the reason TV having 'gaming' mode to turn off time consuming image enhancing algorithm. Refresh rate stay the same, but latency from digital input to physical output (photon) will be lower. My goal is to measure the time that spend from camera shutter complete read the image, up to such image arrived into our application's memory. Before building up my own setup, I firstly tried a [script from github](https://github.com/perrytsao/Webcam-Latency-Measurement)

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/original_webcam.png)

the logic is straightforward:

```
while read camera image
  draw timestamp on camera image
  show this image on screen

```

when I tried this script with my webcam (30FPS), I got 32 milliseconds and 36 milliseconds, and what interested me is the real-time FPS output, it shows 27.x FPS or 31.x FPS. Seems... Perfectly match the latency ?32 x 31 ~ 1000  and 36 x 28 ~ 1000, is this by accident? Let's drawing a diagram to see how different blocks connected together:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/diagram.png)

or in another way:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/original_another_way.png)

The two timestamps appeared on one image, is always the timestamp we mark in the loop,  when we calculate the delta between these two timestamps, of course it's just the time in-between two capture time, has nothing to do with the transfer time! The issue is that the timestamp used as start is bounded to camera frequency, when camera latency is lower than that interval, start timestamp already out-of-date (since no camera update during that period), the measured latency precision also bounded to the interval. 

Original script always give exactly 1 interval delta on my setup, is also useful. It prove that before camera capture next frame, the exactly previous frame already being captured and shown on display, no frames pending in any queue, our capture+display logic is fast enough. Otherwise it will mark a none-previous frame by next timestamp, then two timestamps in one image must have delta > interval , not exactly equals to 1 interval.

Inspired by that script, we should decouple the start timestamp mark display frequency from camera frequency, also refresh it as fast as possible. My monitor worked at 165HZ, much higher than webcam (30), should be good enough for this task.

First Try: Using console text print, it works like this:
  
  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/simple_text.gif)

Result: failed, flushing too fast, camera can't catch clear text at all

Second Try: Spread text along whole line, so individual timestamp will stay stable.  Result: kind of worked 

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/multi_text.gif)

This approach have other drawbacks:
* flushing doesn't aligned to V-sync, captured time is not most accurate
* App run under GUI virtual terminal, which might have it's internal buffering lead extra latency
* GUI output controlled by window manager, hard to reason about buffer queue.
* Manually look into every image required, not automatic

Then I tried to put Linux under VGA/SVGA mode (to get ride of KMS/DRM stack), after some rounds searching with chatgpt/google, I realized such functionality already implemented by graphics card (not monitor), and on UEFI it's replaced by GOP, Not support higher than 60HZ refresh rate is also a major problem. So I looked into KMS/DRM information, it already has everything I need

* complete frame buffer control, no window system/manager in charge.
* atomic flip, allow perfect match to V-sync
* provides notify callback when flip is finished, allow accurate timing recording.
* support OpenGL(ES) painting, GPU still take the heavy lifting
 
There's also a KMS/DRM thin wrapper [SRM](https://cuarzosoftware.github.io/SRM/index.html) allows you to quickly start OpenGL(ES) drawing. It's callback based, assume opengl painting trigger exactly once in-between two flips, thus perfectly align to V-sync (if paint time won't exceed frame interval)

Third Try: This time I use QRcode to display timestamp information on screen, make automatic post-processing possible. Similar to the text painting, QrCode are also placed at different location on screen and stay for a while. With this trick, even monitor flushing at 165 HZ, one QRCode can stay for more than 1/165 second. The more you arrange, the longer it stay. 30 FPS camera also has enough time to capture stable image. otherwise a QRCode may already show on screen and disappeared without camera notice. Since there's still no way to measure the time spend on page flip itself (after we sending flip to kernel, up to the monitor start sending photon for that contents). The best we can do is to use the page flipped callback (of previous frame) timestamp. This will make latency result longer than actual value (1/165 second at most). diagram of my latency measure:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/my_flow.png)


I start with the SRM examples, to recroding the pageFlipped timing, got this plot:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/page-flipped-timing.png)

FPS caluclated from this timing is 165.0786808021504

the monitor information reported by xrandr
```
  2560x1440 (0x1c2) 645.000MHz +HSync -VSync *current +preferred
        h: width  2560 start 2568 end 2600 total 2640 skew    0 clock 244.32KHz
        v: height 1440 start 1446 end 1454 total 1480           clock 165.08Hz

```
FPS calculated from this information should be 645000000 / 2640 / 1480 ~ 165.07985 FPS, differences < 1e-5, should be good enough.

OpenGL(ES) QrCode painting logic is written with help of chatgpt, But testing/debugging KMS/DRM application is quite painful since it takes full control of whole frame buffer (ctrl+alt+FN switching won't work), so I wrote a GLUT entry to test everything under normal x11 environment, once it's done, switching to SRM entry just works. Then I use my phone's 240FPS slow motion to verify such setup actually work (gif play already slow down):

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/phone-slow-motion.gif)


by comparing the frame timestamp (using it's FPS) to the timestamp on every frame, we can test if timestamp is accurate.

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate,r_frame_rate -of default=noprint_wrappers=1 slowmo_clock_boottime.MOV

r_frame_rate=240/1
avg_frame_rate=154080/641 ~ 240.37 FPS
```

Use avg_frame_rate (actual file frame rate) instead of r_frame_rate. Consumer grade slow motion recording usually deployed variable frame rate, 240 is not always the exactly value. By aligning start time of both time series, I got following result :

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/slow-motion-page-flip-diff.png), 

Here we see the jitter between two time series, since monitor refresh timing doesn't aligned to slowmo capture timing, it's possible that the phone capture just appeared content, or capture the very out-of-date content (already stay for 1/165 sec on screen). The slow motion video shows that no more than one new image appear at same time, so now I'm confident to say the KMS/DRM Qrcode flush logic is correct. 

And we also need to verify v4l2 setup, my webcame support variable frame rate, automatically reduce the frame rate if no big motion in scene (and automatically restore FPS if you wave your hand in front), annoying for latency testing.

```
v4l2-ctl --all| grep dynamic_framerate

     exposure_dynamic_framerate 0x009a0903 (bool)   : default=0 value=0

# turn it off by
v4l2-ctl -d /dev/video0 -c exposure_dynamic_framerate=0

```

Then I use my webcam to capture the screen video, calculate the duration from latest qrcode timestamp of frame, to the timestamp of that frame being captured,
I got following plot:


  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/my_latency_30fps.png), 


This data makes more sense, the latency should have jitter just like slowmo-timestamp plot, instead of a fixed value. We have best case 32ms, worst case 51.5 ms and avg 41.2ms. Note, our result is longer than actual value at most 1/165 sec, so all these values are the "worst case" value. So the latency of my webcam will be in range 26ms ~ 51.5ms, the latency came from 2 parts:

1. the time spend on signal travel over usb to our application memory, it depends on streaming data size. It decides the best case latency
2. the camera FPS, It decides the worst case latency


Now let's verify the latency for low FPS setup. By forcing the FPS to 10, we can predict that original script will always give latency that are 1/10 sec. I made change original script to paint qrcode instead of text timestamp, also recording the elapsed time since last time received image. Firstly let's see the time delta between two captures:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/10fps_capture_delta.png), 

the fps is a little slow than 10, 8.9 FPS most of time, Secondly if we compare this data to the delta of two timestamp on image (by qrcode), we will see
 
```
capture delta , qrcode delta
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

this clearly shows that the 'latency' original script measure, is essential the delta between two capture, not the time signal travel to application. Consider a camera that only takes 1 picture every 1 hour, due to the text drawn on image only update once per hour, the latency measured by original script is always an hour. The time signal traveling to our application is much faster, but dominated by 1 hour interval time. So Original script result is only meaningful when transfer latency is much longer than one interval period. (it also link to a table of some cameras result, all latencies are greater than one interval)

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/original_tests.png)


Then measure it with my approach, this time it's more tricky, since the camera doesn't work the exactly way at different FPS. For 30 FPS streaming, even camera can't capture every monitor update, every frame still shows the correct pattern of image: clearest image always appear at bottom right (because we draw new qrcode top-bottom, left-right) but 10FPS is like this:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/10fps_9_qrcode.gif), 

all qrcode appear/disappear at same time, lead lots of empty image. My suspect is that camera shutter/timer doesn't work at constant frequency (as capture delta plot shown, it constantly jumping between two duration). So I increase the number of qrcode grid from 3x3 to 4x4, also increasing the stay time of every qrcode, then the capture like this

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/10fps_16_qrcode.gif), 

still not the correct image pattern, but at least better:

  ![image]({{ site.baseurl }}/images/2026-02-09-journal-on-camera-latency-measure/10fps_latency_plot.png), 

Average latency 82.9 ms, best case 53 ms, worst case 113 ms. So latency range should be 47 ~ 113. Such value seems more matched to original script result because it's dominated by the frequency part of latency.

Side notes: I also tested with realtime kernel, or switching cpu governer (powersaving/performance) didn't see too much changes. Someone 
said that the usb hub directly to CPU should have [lower latency](https://github.com/MariusHeier/cpu-direct-usb), I tried to connect my webcam to 15b6 (AMD CPU-Integrated, CHIP 0 - LOWEST LATENCY Raphael/Granite Ridge USB 3.1 xHCI, Ryzen 7000/9000 Desktop AM5) and 43fc( AMD Chipset CHIP 1 800 Series Chipset USB 3.x XHCI Controller X870/B850 AM5), also don't see any significant differences.


How Nvidia measure input E2E latency? it's called (LDAT)[https://developer.nvidia.com/nvidia-latency-display-analysis-tool], a photon sensor attached in front of monitor, and registered as mouse. It measure the elapsed time
after emulated mouse click up to corresponding flush on monitor, This Digital Foundry Video shows how it works:

https://www.youtube.com/watch?v=TuVAMvbFCW4  at 3:21


