#!/usr/bin/env python3
from Crypto.Cipher import AES
import sys
import colorsys
import simplepyble
import time
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from collections import OrderedDict
import zlib
import sys
import io



SERVICE_UUID             = "000000fa-0000-1000-8000-00805f9b34fb"
WRITE_CMD_UUID           = "0000fa02-0000-1000-8000-00805f9b34fb" # For sending commands to the controller
NOTIFICATION_UUID        = "0000fa03-0000-1000-8000-00805f9b34fb" # The UUID that I think notifications are sent from
MIN_BYTE_VALUE = 0x80 # This seems pretty much static for all packets.  I haven't experimented with it though.

def write_packet(packet):
    #packet = encrypt_aes_ecb(packet)
    peripheral.write_request(SERVICE_UUID, WRITE_CMD_UUID, bytes(packet))

def build_rainbow_colour_list(num=31):
    colour_list = []
    colour_divisions = int(360 / num)
    for i in range(num):
        h = i * colour_divisions
        r, g, b = colorsys.hsv_to_rgb(h / 360, 1, 1)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        colour_list.append((r, g, b))
    print(f"Colour list: {colour_list}")
    return colour_list

def generate_spiral_coordinates(grid_size=32, num_points=500):
    x_center, y_center = grid_size // 2, grid_size // 2
    spiral_coordinates = []

    for t in range(num_points):
        angle = 0.1 * t
        radius = 0.5 * angle

        x = int(x_center + radius * math.cos(angle))
        y = int(y_center + radius * math.sin(angle))

        if 0 <= x < grid_size and 0 <= y < grid_size:
            spiral_coordinates.append((x, y))

    return list(OrderedDict.fromkeys(spiral_coordinates))

def graffiti_paint(rgb_tuple, x, y):
    # Sets a single pixel to a colour and mode
    """
        y (starting at zero) ---------------|
        x (starting at zero) ------------|  |
        blue -------------------------|  |  |
        green ---------------------|  |  |  |
        red --------------------|  |  |  |  |
        header --|------------| |  |  |  |  |
                `0a 00 05 01 00 ff 00 00 1f 1f`
                 0  1  2  3  4  5  6  7  8  9
    """
    graffiti_packet = bytearray.fromhex("0a 00 05 01 00 ff 00 00 1f 1f")
    print(f"X: {x}, Y: {y}")
    print(f"RGB: {rgb_tuple}")
    if x > 31:
        x = 31
    if y > 31:
        y = 31
    r, g, b = rgb_tuple
    graffiti_packet[5] = r
    graffiti_packet[6] = g
    graffiti_packet[7] = b
    graffiti_packet[8] = x
    graffiti_packet[9] = y
    write_packet(graffiti_packet)

def sync_time():
    # Set the time on the device
    current_time = time.localtime(time.time())
    year = current_time.tm_year & 0xff # This is what the Android app does. This suggests that the year is pointless.
    month = current_time.tm_mon
    day = current_time.tm_mday
    dow = current_time.tm_wday + 1 # The controller uses 1-7 for days of the week, but time uses 0-6
    hour = current_time.tm_hour
    minute = current_time.tm_min
    seconds = current_time.tm_sec
    packet = bytearray.fromhex("0b 00 01 80 e7 0c 12 01 0a 26 10")
    packet[3] = MIN_BYTE_VALUE
    packet[4] = year
    packet[5] = month
    packet[6] = day
    packet[7] = dow
    packet[8] = hour
    packet[9] = minute
    packet[10] = seconds
    print(f"Packet: {packet.hex()}")
    write_packet(packet)


def send_reset_command():
    packet = bytearray.fromhex("04 00 03 80")
    write_packet(packet)
    # Maybe that first command is all that's needed?  Try commenting out this second packet below and see if it still works...
    packet = bytearray.fromhex("05 00 04 80 50")
    write_packet(packet)

def switch_on(state):
    packet = bytearray.fromhex("05 00 07 01 01")
    if state is True:
        packet[4] = 1
    else:
        packet[4] = 0
    write_packet(packet)

def string_to_bitmaps(input_string, font_path=None):
    if font_path is None:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_size = 24
    font = ImageFont.truetype(font_path, font_size)
    hex_strings = []
    for char in input_string:
        image = Image.new('1', (16, 32), 0)
        draw = ImageDraw.Draw(image)
        text_width, text_height = draw.textsize(char, font=font)
        text_x = (16 - text_width) // 2
        text_y = (32 - text_height) // 2
        draw.text((text_x, text_y), char, 1, font=font)
        bitmap = image.load()
        byte = 0
        bit_count = 0
        hex_string = "05ffffff" # 05 is the font size (32) and ffffff is fixed
        for y in range(32):
            for x in range(16):
                # Accumulate bits in little-endian order
                byte |= (bitmap[x, y] << bit_count)
                bit_count += 1
                if bit_count == 8 or (x == 15 and y == 31):
                    hex_string += '{:02x}'.format(byte)
                    byte = 0
                    bit_count = 0
        hex_strings.append(hex_string)
    byte_stream = bytearray.fromhex(''.join(hex_strings))
    return byte_stream

def build_string_packet(text_bitmaps, text_mode=0, speed=100, text_colour_mode=1, text_colour=(255,0,0), text_bg_mode=0, text_bg_colour=(0,0,0)):
    # text_bitmaps is a bytearray and we assume it is correctly formatted
    separator = bytearray.fromhex("05 FF FF FF")
    num_chars = text_bitmaps.count(separator)

    text_metadata = bytearray.fromhex("FF FF 00 01 00 00 00 00 00 00 00 00 00 00")
    text_metadata[0] = num_chars.to_bytes(2, byteorder='little')[0]
    text_metadata[1] = num_chars.to_bytes(2, byteorder='little')[1]
    text_metadata[4] = text_mode
    text_metadata[5] = speed
    text_metadata[6] = text_colour_mode
    text_metadata[7] = text_colour[0] # r
    text_metadata[8] = text_colour[1] # g
    text_metadata[9] = text_colour[2] # b
    text_metadata[10] = text_bg_mode
    text_metadata[11] = text_bg_colour[0] # r
    text_metadata[12] = text_bg_colour[1] # g
    text_metadata[13] = text_bg_colour[2] # b

    packet = text_metadata + text_bitmaps

    header = bytearray.fromhex("FF FF 03 00 00 FF FF FF FF FF FF FF FF 00 00 0c")
    total_len = len(packet) + len(header)
    header[0] = total_len.to_bytes(2, byteorder='little')[0]
    header[1] = total_len.to_bytes(2, byteorder='little')[1]
    # header[2] = total_len.to_bytes(4, byteorder='little')[2]
    # header[3] = total_len.to_bytes(4, byteorder='little')[3]

    textmeta_and_bitmaps = len(packet)
    header[5] = textmeta_and_bitmaps.to_bytes(4, byteorder='little')[0]
    header[6] = textmeta_and_bitmaps.to_bytes(4, byteorder='little')[1]
    header[7] = textmeta_and_bitmaps.to_bytes(4, byteorder='little')[2]
    header[8] = textmeta_and_bitmaps.to_bytes(4, byteorder='little')[3]
    crc = zlib.crc32(packet)
    header[9]  = crc.to_bytes(4, byteorder='little')[0]
    header[10] = crc.to_bytes(4, byteorder='little')[1]
    header[11] = crc.to_bytes(4, byteorder='little')[2]
    header[12] = crc.to_bytes(4, byteorder='little')[3]

    return header + packet    

def print_bitmaps(bitmaps):
    for bitmap in bitmaps:
        for row in bitmap:
            print(''.join(['X' if pixel else '.' for pixel in row]))
        print("\n")

def generate_gif_payload(gif_path):
    with Image.open(gif_path) as img:
        print(f"Image size: {img.size}")
        if img.size != (32, 32):
            print("Image is too big.")
            raise Exception("Image is too big")
    
    with open(gif_path, "rb") as f:
        gif_bytes = f.read()
    
    crc = zlib.crc32(gif_bytes)
    print(f"Length: {len(gif_bytes)}")
    print(f"CRC: {crc}")
    return (gif_bytes, crc)

def build_gif_packet(gif_payload):
    crc = gif_payload[1]
    gif_payload = gif_payload[0]
    header = bytearray.fromhex("FF FF 01 00 00 FF FF FF FF FF FF FF FF 05 00 0d")
    header[9]  = crc.to_bytes(4, byteorder='little')[0]
    header[10] = crc.to_bytes(4, byteorder='little')[1]
    header[11] = crc.to_bytes(4, byteorder='little')[2]
    header[12] = crc.to_bytes(4, byteorder='little')[3]

    l = len(gif_payload)
    total_len = l + (len(header) * 2)
    header[5] = total_len.to_bytes(4, byteorder='little')[0]
    header[6] = total_len.to_bytes(4, byteorder='little')[1]
    header[7] = total_len.to_bytes(4, byteorder='little')[2]
    header[8] = total_len.to_bytes(4, byteorder='little')[3]

    print(f"Header: {header.hex()}")
    print(f"Payload: {gif_payload.hex()}")
    print(f"Payload length: {len(gif_payload)}")

    chunks = []
    for i in range(0, len(gif_payload), 4096):
        chunk = gif_payload[i:i+4096]
        chunks.append(chunk)
    
    for i in range(len(chunks)):
        if i > 0: header[4] = 2
        else: header[4] = 0
        chunk_len = len(chunks[i])+len(header)
        header[0] = chunk_len.to_bytes(2, byteorder='little')[0]
        header[1] = chunk_len.to_bytes(2, byteorder='little')[1]

        write_packet(header + chunks[i])
        print(f"\nChunk {i}:")
        print(' '.join(format(x, '02x') for x in header + chunks[i]))
        time.sleep(1)
 

   
def response_decode(response):
    print(f"Response: {response.hex()}")

def connect_to_device(mac_addr):
    print("Connecting to device" + mac_addr)
    idm_device = Peripheral(mac_addr)
    services = idm_device.getServices()
    for service in services:
        print(service)
        characteristics = service.getCharacteristics()  
        for characteristic in characteristics:
            print(characteristic)
        descriptors = service.getDescriptors()
        for descriptor in descriptors:
            print(descriptor)
    return idm_device

def find_devices():
    idotmatrixes = {}
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(10.0)
    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if desc == "Complete Local Name" and value.startswith("LEDnetWF"):
                    print("Found device: %s (%s), RSSI=%d dB" % (dev.addr, value, dev.rssi))
                    idotmatrixes[dev.addr] = dev.rssi

    if len(idotmatrixes) > 0:
        idotmatrixes = dict(sorted(idotmatrixes.items(), key=lambda item: item[1], reverse=True))
        print("\n\n")
        for key, value in idotmatrixes.items():
            print(f"Device: {key}, RSSI: {value}")
    else:
        print("No devices found")

adapters = simplepyble.Adapter.get_adapters()
adapter = adapters[0]

if len(sys.argv) > 1 and sys.argv[1] == "--scan":
    adapter.set_callback_on_scan_start(lambda: print("Scan started"))
    adapter.set_callback_on_scan_stop(lambda: print("Scan stopped"))
    adapter.set_callback_on_scan_found(lambda peripheral: print(f"Found {peripheral.identifier()} [{peripheral.address()}]"))
    adapter.scan_for(5000)
    peripherals = adapter.scan_get_results()
    print("The following devices  were found:")
    for peripheral in peripherals:
        if peripheral.identifier().startswith("IDM-"):
            print(f"\tMAC address: {peripheral.address()}, RSSI: {peripheral.rssi()}")
            manufacturer_data = peripheral.manufacturer_data()
            for manufacturer_id, value in manufacturer_data.items():
                print(f"\t\tManufacturer ID: {manufacturer_id}")
                print(f"\t\tManufacturer data: {value}")
                print(' '.join(format(x, '02x') for x in value))
elif len(sys.argv) > 1 and sys.argv[1] == "--connect":
    # There are no examples of how to instantiate a peripheral object from a mac address
    # it probably can be done, but I can't work it out from the source, so for now
    # just use scan to find it by name
    print("Scanning for devices")
    adapter.scan_for(2000)
    peripherals = adapter.scan_get_results()
    for peripheral in peripherals:
        if peripheral.identifier().startswith("IDM-"):
            # this will do
            peripheral.connect()
            print(f"Connected to {peripheral.identifier()}.  MTU: {peripheral.mtu()}")
            time.sleep(3)
            try:
                services = peripheral.services()
                for service in services:
                    print(f"Service: {service.uuid()}")
                    for characteristic in service.characteristics():
                        print(f"\tCharacteristic: {characteristic.uuid()}")
                        for descriptor in characteristic.descriptors():
                            print(f"\t\tDescriptor: {descriptor.uuid()}")
                peripheral.notify(SERVICE_UUID, NOTIFICATION_UUID, response_decode)
                print("Turning on")
                switch_on(True)
                time.sleep(1)
                print("Syncing time")
                sync_time()
                
                #spiral = generate_spiral_coordinates()
                #print(spiral)
                # for each in spiral:
                #     graffiti_paint((random.randint(0,255), random.randint(0,255), random.randint(0,255)), each[0], each[1])
                # #    time.sleep(0.1)
                # time.sleep(5)
                text_packet = build_string_packet(string_to_bitmaps("It's Christmas!"), text_mode=1, text_colour=(random.randint(0,255),random.randint(0,255),random.randint(0,255)), text_colour_mode=1)
                write_packet(text_packet)
                time.sleep(5)
                g = generate_gif_payload("assets_test/luigi32.gif")
                build_gif_packet(g)
                time.sleep(5)
                print("Resetting device...")
                send_reset_command()
                #print("Turning off")
                #switch_on(False)
            finally:
                peripheral.disconnect()
else:
    print("Pass in either --scan or --connect")
