# iDotMatrix

Here we go again.

This time is an iDotMatix device.

This device is a 32 by 32 RGB matrix.  A quick look at the app suggests that this uses the same controller as the iDeal LEDs from last time.  Result if that is true.

Looking at the initial packets says that these are not encrypted.  Let's find out.

## On & Off

Nice and simple this time:
```text
0b000180e70c12010a2610
0500070100
0500070101
0500070100
0500070101
0500070100
0500070101
0500070100
0500070101
0500040101
```

`On` : `05 00 07 01 01`
`Off`: `05 00 07 01 00`

TODO: There is some initialisation to be decoded still.
What does `0b 00 01 80 e7 0c 12 01 0a 26 10` do?

```text
11 0 1 128 231 12 18 1 10 38 16` in decimal.
               |  |  | |  |  |
               |  |  | |  |  L sec
               |  |  | |  L min
               |  |  | L hour
|----| header  |  |  L DOW (Monday)
               |  L day
               L month
            L how is this being convert to year?    
        L min byte value in Java is -128 so we've lost the sign? Why is this helpful?
```

## DIY mode

This lets you draw a pattern on the screen.  You use the app to trace out the pattern and choose the colours.

```text
0a00050100ff00000001
0a00050100ff00000001
0a00050100ff00000003
0a00050100ff00000002
0a00050100ff00000001
...
0a00050100ff00001f1f
0a00050100ff00001e1f
0a00050100ff00001e1e
0a00050100ff00001e1f
0a00050100ff00001f1f
0a00050100ff00001e1f
0a00050100ff00001e1e
0a00050100ff00001e1e
```

This looks pretty easy too.  In fact, I'm going to just assume that this is what I think it is and not do more testing. I started top right and ended bottom left drawing red pixels.

y (starting at zero) ---------------|
x (starting at zero) ------------|  |
blue -------------------------|  |  |
green ---------------------|  |  |  |
red --------------------|  |  |  |  |
header --|------------| |  |  |  |  |
        `0a 00 05 01 00 ff 00 00 1f 1f`

Let's write a function to draw a spiral in red in the `idotmatrix_controller.py`.

