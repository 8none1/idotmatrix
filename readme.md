# iDotMatrix

Here we go again.

This time is an iDotMatrix device.

This device is a 32 by 32 RGB matrix.  A quick look at the app suggests that this uses the same controller as the iDeal LEDs from last time.  Result if that is true.

Looking at the initial packets says that these are not encrypted.  Let's find out.

There is another, much better looking, project to control these devices here:  https://github.com/derkalle4/python3-idotmatrix-client


## On & Off


`On` : `05 00 07 01 01`

`Off`: `05 00 07 01 00`


## Set time and date

```text
11 0 1 128 231 12 18 1 10 38 16` in decimal.
               |  |  | |  |  |
               |  |  | |  |  L sec
               |  |  | |  L min
               |  |  | L hour
|----| header  |  |  L DOW (Monday)
               |  L day
               L month
            L how is this being convert to year?    Answer: badly.
        L min byte value in Java is -128 so we've lost the sign? Why is this helpful?
```

The year seems to be a straight conversion to a byte.  i.e. decimal 2023 & 0xFF = decimal 231.
So... maybe the year is irrelevant?  I don't imagine it's really needed for anything.

## Graffiti mode

This lets you draw a pattern on the screen.  You use the app to trace out the pattern and choose the colours.

```text
y (starting at zero) ---------------|
x (starting at zero) ------------|  |
blue -------------------------|  |  |
green ---------------------|  |  |  |
red --------------------|  |  |  |  |
header --|------------| |  |  |  |  |
        `0a 00 05 01 00 ff 00 00 1f 1f`
```

Let's write a function to draw a spiral in red in the `idotmatrix_controller.py`.

It works!

## Text

Text is a series of bitmaps for each letter.

 - The first byte of a long payload is the total length including the length byte
 - At font size "32" each character is 16 pixels wide and 32 high
 - It appears that each character of the text is sent as it's own bitmap.  So if you have a string of 5 characters, 5 sets of bitmaps are sent
 - The bitmap format is row major, little endian
 - `plot_hex_grid.py` is capable of decoding the bytes in to a bitmap which looks like it should
 - Java function is perhaps `` public void sendTextTo3232(BleDevice bleDevice, Material material, int i, TextAgreementListener textAgreementListener)``


Handy tool:  http://dotmatrixtool.com/#



### Text payload

#### Header 1

```text
                         0 1  2  3  4  5 6 7 8  9101112  1314 15
                         6200 03 00 00 52000000 81866079 0000 0c [16 removed see below] 05ffffff [deleted]
length ------------------|||| |  |  |  |------| |------| |--| |  Length is the total length of all bytes including any continuation packets. Bytes little endian.
three ------------------------|  |  |  |      | |      | |  | |
zero ----------------------------|  |  |      | |      | |  | |
maybe continuation marker? if >4096-|  |      | |      | |  | |
length of next header plus bitmaps --- |------| |      | |  | | i.e. total length minus 16
crc32 spanning 4 bytes (char data and the below)|------| |  | |
if `thing` is 12, then 00,00 else something about time---|--| |
`thing` ------------------------------------------------------|

```

#### Header 2 - Text Metadata

```text
                                  0 1  2  3  4  5  6  7  8  9  10 11 12 13   
[16 bytes deleted as seen above ] 0100 00 01 00 64 01 00 00 ff 00 00 00 00 05ffffff [deleted]
length of char array (one char)---|||| |  |  |  |  |  |  |  |  |  |  |  |  |
zero ----------------------------------|  |  |  |  |  |  |  |  |  |  |  |  |
one --------------------------------------|  |  |  |  |  |  |  |  |  |  |  |
text mode -----------------------------------|  |  |  |  |  |  |  |  |  |  |
speed ------------------------------------------|  |  |  |  |  |  |  |  |  |
textcolourmode ------------------------------------|  |  |  |  |  |  |  |  |
red   ------------------------------------------------|  |  |  |  |  |  |  |
green   -------------------------------------------------|  |  |  |  |  |  |
blue   -----------------------------------------------------|  |  |  |  |  |
text background col mode --------------------------------------|  |  |  |  |
bg r -------------------------------------------------------------|  |  |  |
bg g ----------------------------------------------------------------|  |  |
bg b -------------------------------------------------------------------|  |
this is the start the character bitmap   ----------------------------------| 
```

The 0x05 (or a 6) means that the font size (and so the bitmap size?) is "32".  A 2 or a 3 would be for size "16".
Then three bytes of 0xFF are added.  `jadx` shows this as `-1`.

#### CRC32

The checksum (bytes `9` to `12` (zero index)) are the CRC32 of the text metadata header and *all* of the bitmaps (even if the bitmaps go in to a new BLE packet).
So take the entire payload from the byte after `0c` (the end of the first header) to the end.  Do a CRC32 on it, convert it to hex and you might get: `49317daa`.
In the payload the CRC32 would be `aa 7d 31 49` (i.e. little endian).

### multi character text

You send multiple characters one at a time.  Each character starts with a header. `05FFFFFF` - where the `05` indicates the size. 5 is 32 bits.

The maximum payload size is 4kB. I haven't implemented anything to test this for text, but it works for GIFs.  See below.

### Text Mode

```text
0 - fixed
1 - left to right scroll
2 - right to left and letters come in the opposite order.  Must be for RTL languages?
3 - up scroll
4 - down scroll
5 - strobe
6 - fade
7 - falling blocks
8 - laser
```

I'm stopping here.  Last time I experimented with a set of lights it ended badly.

### Text Colour Mode

```text
0 - ?
1 - Fixed
2 - Blue to red gradient
3 - kinda pastels gradient
4 - Pink to orange gradient
5 - ?
```

This is all I've tested so far.  Please update if you have others.

### Text Background Mode

```text
0 - Off
1 - Solid colour
```

## GIFs

My device is 32 x 32 pixels.  All GIFs need to be 32 x 32.  You can use [Gifsicle](https://www.lcdf.org/gifsicle/man.html) to batch resize.
Each gif upload starts with a master header.  The payload must be chunked in to 4k blocks.  At the start of each 4k block is a secondary header.
The payload does not count towards the 4k chunk size it seems.  So 4096 + 16 bytes total size.

When you have finished sending one block you should wait for confirmation from the device via a notification `0500010001`.  Or, much easier, just sleep for a second.
When the upload is complete you should get a `0500010003`.  I haven't implemented any kind of flow control to test this yet.

There is a very rudimentary implementation in the `idotmatrix_controller.py` script.

### Master header

```text
                                         0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 
                                         10 10 01 00 00 b9 18 00 00 db 42 cb 14 05 00 0d
Payload size for this block inc header --|---| |  |  |  |--------|  |---------| |------|    
fixed 01 --------------------------------------|  |  |  |        |  |         | |      |
fixed 00 -----------------------------------------|  |  |        |  |         | |      | 
indications multi chunk. 0 = 1 chunk 2 = > 1 --------|  |        |  |         | |      |
total payload size inc headers over all chunks  --------|--------|  |         | |      |
CRC32 whole payload only, not headers ------------------------------|---------| |      |
fixed? -------------------------------------------------------------------------|------|
```

### Secondary headers

```text
                                         c9 08 01 00 02 b9 18 00 00 db 42 cb 14 05 00 0d
Payload size for this block inc header --|---| |  |  |  |---------| |---------| |------|    
fixed 01 --------------------------------------|  |  |  |         | |         | |      |
fixed 00 -----------------------------------------|  |  |         | |         | |      | 
multi chunk indication as above ---------------------|  |         | |         | |      |
total payload inc headers over all chunks size size ----|---------| |         | |      |
CRC32 whole payload only, not headers ------------------------------|---------| |      |
fixed? something about `timeSign`? doesnt make sense ---------------------------|------|
```

## Other projects that might be of interest

- [iDotMatrix](https://github.com/8none1/idotmatrix)
- [Zengge LEDnet WF](https://github.com/8none1/zengge_lednetwf)
- [iDealLED](https://github.com/8none1/idealLED)
- [BJ_LED](https://github.com/8none1/bj_led)
- [ELK BLEDOB](https://github.com/8none1/elk-bledob)
- [HiLighting LED](https://github.com/8none1/hilighting_homeassistant)
