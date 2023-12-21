# iDotMatrix

Here we go again.

This time is an iDotMatrix device.

This device is a 32 by 32 RGB matrix.  A quick look at the app suggests that this uses the same controller as the iDeal LEDs from last time.  Result if that is true.

Looking at the initial packets says that these are not encrypted.  Let's find out.

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

Text looks like it is a bitmap of the whole screen. I will keep a list of discoveries here as I go:

 - The first byte of a long payload is the total length including the length byte (I think)
 - A single line on the display has to have the same colour.  That is, each line must have a colour component for the whole line
 - At font size "32" each character is 16 pixels wide and 32 high
 - It appears that each character of the text is sent as it's own bitmap.  So if you have a string of 5 characters, 5 sets of bitmaps are sent
 - The bitmap format is row major, little endian
 - `plot_hex_grid.py` is capable of decoding the bytes in to a bitmap which looks like it should
 - Java function is perhaps `` public void sendTextTo3232(BleDevice bleDevice, Material material, int i, TextAgreementListener textAgreementListener)``


Handy tool:  http://dotmatrixtool.com/#



### Mostly decoded text payload

Try and decode the bytes using the Java code:

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
this is the start the character bitmaps  ----------------------------------| 
```

The 0x05 (or a 6) means that the font size (and so the bitmap size?) is "32".  A 2 or a 3 would be for size "16".
Then three bytes of 0xFF are added.  `jadx` shows this as `-1`.

#### CRC32

The checksum (bytes `9` to `12` (zero index)) are the CRC32 of the text metadata header and *all* of the bitmaps (even if the bitmaps go in to a new BLE packet).
So take the entire payload from the byte after `0c` (the end of the first header) to the end.  Do a CRC32 on it, convert it to hex and you might get: `49317daa`.
In the payload the CRC32 would be `aa 7d 31 49` (i.e. little endian).

### multi character text

```text
72 01 03 00 00 62 01 00 00 11 cf 8d 01 00 00 0c 050000010064010000ff00000000 05 ff ff ff 000000000000000000001c001c001c001c001c001c001c009c0fdc1f7c3c3c383c381c381c381c381c381c381c381c381c381c3800000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f80f3c1c1c180e38fe3ffe3f0e000e000e381c383c1cf80fe00300000000000000000000000005ffffff0000000000000000000080038003800380038003800380038003800380038003800380038003800380038003800380038003800300000000000000000000000005ffffff0000000000000000000080038003800380038003800380038003800380038003800380038003800380038003800380038003800300000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f00f381c1c380e700e700e700e700e700e701c38381cf00fe007000000000000000000000000
```

I think that the packets are just split in to maximum 4k chunks.

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

