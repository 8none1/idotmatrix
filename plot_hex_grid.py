#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont
import zlib

def plot_hex_grid(hex_string, width, height, little_endian=False):
    l = len(hex_string)
    byte_data = bytes.fromhex(hex_string)
    grid = [['.' for _ in range(width)] for _ in range(height)]
    # Iterate through each byte in the data
    for i in range(0, len(byte_data), 2):
        # Convert two bytes to a 16-bit integer
        if little_endian:
            pixel_value = int.from_bytes(byte_data[i:i + 2], byteorder='little')
        else:
            pixel_value = int.from_bytes(byte_data[i:i + 2], byteorder='big')
        # Iterate through each bit in the 16-bit integer
        for j in range(16):
            # Extract the j-th bit
            bit = (pixel_value >> (15 - j)) & 1
            # Map 1 to 'X' and 0 to '.'
            if little_endian:
                grid[i // 2][width - 1 - j] = 'X' if bit else '.'
            else:
                grid[i // 2][j] = 'X' if bit else '.'
    for row in grid:
        print(''.join(row))


def set_text(text, text_colour=(255,0,0), text_colour_effect=0, background_colour=(0,0,0), background_colour_effect=0, speed=50,font_path=None):
    # Set default font if none provided
    if font_path is None:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    # Adjust font size as needed to fit in 16x32 grid
    font_size = 24  # This may need tweaking depending on the font and desired appearance
    font = ImageFont.truetype(font_path, font_size)
    bitmaps = []
    for char in text:
        # Create image with a 16 (width) x 32 (height) grid
        image = Image.new('1', (16, 32), 0) # Background is black 0 - could be changed to 1 for white for inverted text
        draw = ImageDraw.Draw(image)
        # Calculate text position to center it in the grid
        text_width, text_height = draw.textsize(char, font=font)
        text_x = (16 - text_width) // 2
        text_y = (32 - text_height) // 2
        # Draw the character
        draw.text((text_x, text_y), char, 1, font=font) # 1 for white text
        # Convert to bitmap and add to list
        bitmap = image.load()
        bitmaps.append([[bitmap[x, y] for x in range(16)] for y in range(32)])
        print(bitmaps)
    return bitmaps

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
        hex_string = ""
        hex_string+= "05ffffff"


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

    return hex_strings

def iterate_values(hex_string):
    # Convert hex string to bytes
    # This is super janky and needs to parse the strings much more reliably.  But we only need to encode really, so not really bothered.
    byte_data = bytes.fromhex(hex_string)
    print(f"Length of byte data: {len(byte_data)}")
    if byte_data[0] == 0xff:
        # This indicates that it is a continuation of the previous payload I think. Hack it to make it work.
        byte_data = byte_data[1:]
        # and pre-pend the marker
        byte_data = bytes.fromhex("05ffffff") + byte_data

    # Find occurrences of "05ffffff"
    pattern = bytes.fromhex("05ffffff")
    start_index = 0
    occurrences = []

    while start_index < len(byte_data):
        index = byte_data.find(pattern, start_index)
        print(index)
        if index == -1:
            break
        occurrences.append(index)
        start_index = index + len(pattern)

    # Extract bytes for each occurrence
    terminator_pattern = bytes.fromhex("05ffff")
    for i, start in enumerate(occurrences):
        end = occurrences[i + 1] if i + 1 < len(occurrences) else len(byte_data)
        result_bytes = byte_data[start + len(pattern):end]
        # Strip and dangling separator bytes
        index = result_bytes.find(terminator_pattern)
        print(f"Index: {index}")
        if index != -1:
            result_bytes = result_bytes[:index]
        result_hex_string = ''.join(format(byte, '02X') for byte in result_bytes)
        print(result_hex_string)
        plot_hex_grid(result_hex_string, 16, 32, little_endian=True)


def print_bitmaps(bitmaps):
    for bitmap in bitmaps:
        for row in bitmap:
            print(''.join(['X' if pixel else '.' for pixel in row]))
        print("\n")

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


# Copy and paste a line from tshark which contains only the values
# The we will extract the letter and print it on a grid maybe.

# an actual hash #hash_value = "62000300005200000032a4a8c500000c010000010000010000ff0000000005ffffff00000000000000000000000020102010201020102010fe7ffe7ffe7f100810081008100810081008fe7ffe7ffe7f180c08040804080408040000000000000000"
# my generated text:                                                                       "05ffffff00000000000000000000000000000000000000000000303030303030303030303ff03ff030303030303030303030000000000000000000000000000000000000"
# a w # hash_value    = "620003000052000000b2f4c89a00000c010000010000010000ff0000000005ffffff000000000000000000008ee38ee38ee38ee39c739c729c72dc76dc76dc76dc76d836d836f83ef83ef83e783c783c701c701c701c000000000000000000000000"
# hash_value = "620003000052000000934dbb8c00000c010000010000010000ff0000000005ffffff00000000000000000000e007f00f381e1c1c1c380c380e380e000e000e000e3f0e3f0e380e380e380e381c381c3c383ef03fe033000000000000000000000000"
multi_char = "0a03030000fa0200000914ec8300000c0b000001016201ff00000000000005ffffff000000000000000000001c001c001c001c001c001c001c009c0fdc1f7c3c3c383c381c381c381c381c381c381c381c381c381c3800000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f80f3c1c1c180e38fe3ffe3f0e000e000e381c383c1cf80fe00300000000000000000000000005ffffff0000000000000000000080038003800380038003800380038003800380038003800380038003800380038003800380038003800300000000000000000000000005ffffff0000000000000000000080038003800380038003800380038003800380038003800380038003800380038003800380038003800300000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f00f381c1c380e700e700e700e700e700e701c38381cf00fe00700000000000000000000000005ffffff0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005ffffff0000000000000000000000000000e000e000e000e000e000fe1ffe1fe000e000e000e000e000e000e000e000e000e021c03f003f00000000000000000000000005ffff"
continuation = "ff000000000000000000001c001c001c001c001c001c001c009c0fdc1f7c3c3c383c381c381c381c381c381c381c381c381c381c3800000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f80f3c1c1c180e38fe3ffe3f0e000e000e381c383c1cf80fe00300000000000000000000000005ffffff000000000000000000000000000000000000000000000000380e380fb80ff801f80078003800380038003800380038003800380000000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f80f3c1c1c180e38fe3ffe3f0e000e000e381c383c1cf80fe003000000000000000000000000"
#plot_hex_grid(trimmed_hash_value, 16, 32, little_endian=True)

#iterate_values(multi_char)
#iterate_values(continuation)
#plot_hex_grid("0000000000000000000000000000e000e000e000e000e000fe1ffe1fe000e000e000e000e000e000e000e000e000e021c03f003f000000000000000000000000", 16, 32, little_endian=True)

a = set_text("hello")
print_bitmaps(a)

# hex_output = string_to_bitmaps("Hello")
# for i, hex_string in enumerate(hex_output):
#     print(f"Character {i}: {hex_string}")

# multi_char = ''.join([''.join(lst) for lst in hex_output])
# print(multi_char)
# #plot_hex_grid("000000000000000000000000000000000000000000000c0c0c0c0c0c0c0c0c0cfc0ffc0f0c0c0c0c0c0c0c0c0c0c000000000000000000000000000000000000", 16, 32, little_endian=True)

# iterate_values(multi_char)

# test_packet_from_device = """8202030000720200009f93adf900000c09000001016401ff00000000000005ffffff000000000000000000000000000000000000000000000000e007f80f3c1c1c380e380e000e000e000e380e381c3c3c1cf80fe00300000000000000000000000005ffffff000000000000000000001c001c001c001c001c001c001c009c0fdc1f7c3c3c383c381c381c381c381c381c381c381c381c381c3800000000000000000000000005ffffff000000000000000000000000000000000000000000000000380e380fb80ff801f80078003800380038003800380038003800380000000000000000000000000005ffffff0000000000000000000080038003800300000000000000008003800380038003800380038003800380038003800380038003800300000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f81f3c3c1c381c003c00f807e01f003c1c381c38383cf81fe00700000000000000000000000005ffffff0000000000000000000000000000e000e000e000e000e000fe1ffe1fe000e000e000e000e000e000e000e000e000e021c03f003f00000000000000000000000005ffffff000000000000000000000000000000000000000000000000ce79feff9ee78ee38ee38ee38ee38ee38ee38ee38ee38ee38ee38ee300000000000000000000000005ffff
# ff000000000000000000000000000000000000000000000000c00ff01f783c38380038003ee03ff83b3c381c381c3c3c3ef83ff07900000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f81f3c3c1c381c003c00f807e01f003c1c381c38383cf81fe007000000000000000000000000
# """

# bitmap_from_test_packet = """05ffffff000000000000000000000000000000000000000000000000e007f80f3c1c1c380e380e000e000e000e380e381c3c3c1cf80fe00300000000000000000000000005ffffff000000000000000000001c001c001c001c001c001c001c009c0fdc1f7c3c3c383c381c381c381c381c381c381c381c381c381c3800000000000000000000000005ffffff000000000000000000000000000000000000000000000000380e380fb80ff801f80078003800380038003800380038003800380000000000000000000000000005ffffff0000000000000000000080038003800300000000000000008003800380038003800380038003800380038003800380038003800300000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f81f3c3c1c381c003c00f807e01f003c1c381c38383cf81fe00700000000000000000000000005ffffff0000000000000000000000000000e000e000e000e000e000fe1ffe1fe000e000e000e000e000e000e000e000e000e021c03f003f00000000000000000000000005ffffff000000000000000000000000000000000000000000000000ce79feff9ee78ee38ee38ee38ee38ee38ee38ee38ee38ee38ee38ee300000000000000000000000005ffff
# ff000000000000000000000000000000000000000000000000c00ff01f783c38380038003ee03ff83b3c381c381c3c3c3ef83ff07900000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f81f3c3c1c381c003c00f807e01f003c1c381c38383cf81fe007000000000000000000000000"""

# test_text_packet_generator = build_string_packet(bytearray.fromhex(bitmap_from_test_packet), text_mode=1, text_colour_mode=1, text_colour=(255,0,0), text_bg_mode=0, text_bg_colour=(0,0,0))

# print(' '.join([f'{byte:02X}' for byte in bytearray.fromhex(test_packet_from_device)]))
# print(' '.join([f'{byte:02X}' for byte in test_text_packet_generator]))
