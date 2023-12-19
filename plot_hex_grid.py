#!/usr/bin/env python3

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


def iterate_values(hex_string):
    # Convert hex string to bytes
    byte_data = bytes.fromhex(hex_string)

    # Find occurrences of "05ffffff"
    pattern = bytes.fromhex("05ffffff")
    start_index = 0
    occurrences = []

    while start_index < len(byte_data):
        index = byte_data.find(pattern, start_index)
        if index == -1:
            break
        occurrences.append(index)
        start_index = index + len(pattern)

    # Extract bytes for each occurrence
    for i, start in enumerate(occurrences):
        end = occurrences[i + 1] if i + 1 < len(occurrences) else len(byte_data)
        result_bytes = byte_data[start + len(pattern):end]
        result_hex_string = ''.join(format(byte, '02X') for byte in result_bytes)
        #print(result_hex_string)
        plot_hex_grid(result_hex_string, 16, 32, little_endian=True)


# Copy and paste a line from tshark which contains only the values
# The we will extract the letter and print it on a grid maybe.

# an actual hash #hash_value = "62000300005200000032a4a8c500000c010000010000010000ff0000000005ffffff00000000000000000000000020102010201020102010fe7ffe7ffe7f100810081008100810081008fe7ffe7ffe7f180c08040804080408040000000000000000"
# a w # hash_value    = "620003000052000000b2f4c89a00000c010000010000010000ff0000000005ffffff000000000000000000008ee38ee38ee38ee39c739c729c72dc76dc76dc76dc76d836d836f83ef83ef83e783c783c701c701c701c000000000000000000000000"
# hash_value = "620003000052000000934dbb8c00000c010000010000010000ff0000000005ffffff00000000000000000000e007f00f381e1c1c1c380c380e380e000e000e000e3f0e3f0e380e380e380e381c381c3c383ef03fe033000000000000000000000000"
multi_char = "72010300006201000011cf8d0100000c050000010064010000ff0000000005ffffff000000000000000000001c001c001c001c001c001c001c009c0fdc1f7c3c3c383c381c381c381c381c381c381c381c381c381c3800000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f80f3c1c1c180e38fe3ffe3f0e000e000e381c383c1cf80fe00300000000000000000000000005ffffff0000000000000000000080038003800380038003800380038003800380038003800380038003800380038003800380038003800300000000000000000000000005ffffff0000000000000000000080038003800380038003800380038003800380038003800380038003800380038003800380038003800300000000000000000000000005ffffff000000000000000000000000000000000000000000000000e007f00f381c1c380e700e700e700e700e700e701c38381cf00fe007000000000000000000000000"
#plot_hex_grid(trimmed_hash_value, 16, 32, little_endian=True)

iterate_values(multi_char)