from PIL import Image
import struct


HEADER_SIZE = 4  # 4 bytes to store payload length


def bytes_to_bits(data):
    """Convert bytes into a sequence of bits."""

    bits = []

    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    return bits


def bits_to_bytes(bits):
    """Convert a sequence of bits back into bytes."""

    if len(bits) % 8 != 0:
        raise ValueError("Number of bits must be a multiple of 8.")

    result = bytearray()

    for i in range(0, len(bits), 8):

        byte = 0

        for bit in bits[i:i + 8]:
            byte = (byte << 1) | bit

        result.append(byte)

    return bytes(result)


def calculate_capacity(image):
    """Calculate maximum payload capacity in bytes."""

    width, height = image.size

    total_bits = width * height * 3

    total_bytes = total_bits // 8

    # Reserve space for the 4-byte header
    return total_bytes - HEADER_SIZE


def hide_data(input_image, output_image, data):
    """Hide byte data inside an RGB image using LSB."""

    image = Image.open(input_image).convert("RGB")

    # Check capacity
    capacity = calculate_capacity(image)

    if len(data) > capacity:
        raise ValueError(
            f"Payload too large. Maximum capacity is "
            f"{capacity} bytes."
        )

    # Store payload length in exactly 4 bytes
    header = struct.pack(">I", len(data))

    # Header + actual data
    payload = header + data

    # Convert everything into bits
    payload_bits = bytes_to_bits(payload)

    pixels = list(image.getdata())

    new_pixels = []

    bit_index = 0

    for pixel in pixels:

        new_pixel = list(pixel)

        for channel in range(3):

            if bit_index < len(payload_bits):

                # Clear LSB
                new_pixel[channel] &= 254

                # Put our data bit
                new_pixel[channel] |= payload_bits[bit_index]

                bit_index += 1

        new_pixels.append(tuple(new_pixel))

    # Create stego image
    stego_image = Image.new("RGB", image.size)

    stego_image.putdata(new_pixels)

    # Save as PNG
    stego_image.save(output_image, format="PNG")

    print("Data hidden successfully.")
    print("Payload size:", len(data), "bytes")
    print("Image capacity:", capacity, "bytes")


def extract_data(image_path):
    """Extract hidden byte data from an LSB stego image."""

    image = Image.open(image_path).convert("RGB")

    pixels = list(image.getdata())

    # First extract 32 bits = 4-byte header
    header_bits = []

    for pixel in pixels:

        for channel in range(3):

            header_bits.append(pixel[channel] & 1)

            if len(header_bits) == HEADER_SIZE * 8:
                break

        if len(header_bits) == HEADER_SIZE * 8:
            break

    header = bits_to_bytes(header_bits)

    payload_length = struct.unpack(">I", header)[0]

    print("Hidden payload size:", payload_length, "bytes")

    # Extract payload
    total_bits_needed = (
        HEADER_SIZE + payload_length
    ) * 8

    all_bits = []

    for pixel in pixels:

        for channel in range(3):

            all_bits.append(pixel[channel] & 1)

            if len(all_bits) == total_bits_needed:
                break

        if len(all_bits) == total_bits_needed:
            break

    if len(all_bits) < total_bits_needed:
        raise ValueError("Incomplete hidden data.")

    payload_bits = all_bits[HEADER_SIZE * 8:]

    return bits_to_bytes(payload_bits)