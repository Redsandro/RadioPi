RadioPi
=======
A simple loop to control the MPD backend on my Raspberry Pi internet radio.

I've been using this for years, but I'm building a new one with a little LCD.

![Prototype](https://raw.github.com/Redsandro/RadioPi/master/raspberry.jpg)

There are two GPIO buttons for prev/next. Pressing both resets MPD (clears playlist and loads "Internet Radio.m3u").
This is convenient after playing music files from the library using a client such as GMPC or MPDroid.

__LCD__

New titles will scroll once, then a clock appears for convenience.

---

####Prerequisites

`crontab -e`:

```
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
@reboot python /root/RadioPi/radio.py
```

I had my `alsamixer` on max and I destroyed one amp. Better tone it down somewhat.

`/etc/rc.local`:

```
# Set volume
# You would think 95%, which is 100 in the mixer (100% is 120), is a good default.
# But cheap ass amps damage with this strong signal.
/usr/bin/amixer set 'PCM',0 80% > /dev/null
```

####License

Copyright 2013 – 2016 Sander Steenhuis [@Redsandro](https://twitter.com/Redsandro)

Distributed under the GPL v2 license.
