"""
Generates valid PNG icons for Trakerz PWA using only Python standard library.
"""
import zlib
import struct
from pathlib import Path

def create_png(width: int, height: int, filename: Path):
    # Palette colors:
    # Background: Indigo #4f46e5 (79, 70, 229)
    # Circle accent: Light purple #818cf8 (129, 140, 248)
    # Symbol: White #ffffff (255, 255, 255)
    
    raw_data = bytearray()
    cx, cy = width // 2, height // 2
    r_outer = width * 0.44
    r_inner = width * 0.36
    
    for y in range(height):
        raw_data.append(0)  # filter type 0 (None)
        for x in range(width):
            dist_sq = (x - cx) ** 2 + (y - cy) ** 2
            
            # Corner rounded rect background
            corner_r = width * 0.22
            in_rect = (
                (corner_r <= x <= width - corner_r) or
                (corner_r <= y <= height - corner_r) or
                ((min(abs(x - corner_r), abs(x - (width - corner_r))) ** 2 +
                  min(abs(y - corner_r), abs(y - (height - corner_r))) ** 2) <= corner_r ** 2)
            )
            
            if not in_rect:
                # Transparent outside rounded rect
                raw_data.extend((0, 0, 0, 0))
                continue
                
            # Base indigo background
            red, green, blue, alpha = 79, 70, 229, 255
            
            # Decorative inner ring
            if r_inner**2 <= dist_sq <= r_outer**2:
                red, green, blue = 129, 140, 248
                
            # "T" glyph in white
            # Crossbar of T
            bar_top = int(cy - height * 0.22)
            bar_bottom = int(cy - height * 0.10)
            bar_left = int(cx - width * 0.24)
            bar_right = int(cx + width * 0.24)
            
            # Stem of T
            stem_top = bar_bottom
            stem_bottom = int(cy + height * 0.24)
            stem_left = int(cx - width * 0.08)
            stem_right = int(cx + width * 0.08)
            
            # Rupee / Currency accent dot
            dot_cx = int(cx + width * 0.20)
            dot_cy = int(cy + height * 0.18)
            dot_r = width * 0.06
            in_dot = ((x - dot_cx)**2 + (y - dot_cy)**2) <= dot_r**2
            
            if (bar_left <= x <= bar_right and bar_top <= y <= bar_bottom) or \
               (stem_left <= x <= stem_right and stem_top <= y <= stem_bottom) or \
               in_dot:
                red, green, blue = 255, 255, 255
                
            raw_data.extend((red, green, blue, alpha))

    # Compress IDAT chunk
    compressed = zlib.compress(bytes(raw_data), 9)

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xffffffff)
        return length + chunk_type + data + crc

    # PNG Signature
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png.extend(chunk(b"IHDR", ihdr_data))
    # IDAT
    png.extend(chunk(b"IDAT", compressed))
    # IEND
    png.extend(chunk(b"IEND", b""))

    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_bytes(png)
    print(f"Generated icon: {filename} ({width}x{height})")

if __name__ == "__main__":
    icons_dir = Path(__file__).resolve().parent
    create_png(192, 192, icons_dir / "icon-192.png")
    create_png(512, 512, icons_dir / "icon-512.png")
