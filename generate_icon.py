#!/usr/bin/env python3
"""Generate app icon for broom-widget using PyObjC."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Foundation import NSMakeRect, NSMakeSize, NSPoint
from AppKit import (
    NSImage, NSBitmapImageRep, NSGraphicsContext,
    NSBezierPath, NSColor, NSDeviceRGBColorSpace,
    NSBitmapImageFileTypePNG,
)
import objc

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon")
os.makedirs(ICON_DIR, exist_ok=True)

def draw_icon(size):
    """Draw icon at given size."""
    bmp = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, size, size, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0,
    )
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(bmp)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.setCurrentContext_(ctx)
    
    s = size  # scale factor
    cx, cy = s/2, s/2
    
    # Background rounded square
    margin = s * 0.04
    radius = s * 0.2
    bg = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.08, 0.08, 0.15, 1.0)
    bg.setFill()
    bg_rect = NSMakeRect(margin, margin, s - margin*2, s - margin*2)
    bg_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bg_rect, radius, radius)
    bg_path.fill()
    
    # Subtle gradient overlay
    grad = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.12, 0.12, 0.22, 0.5)
    grad.setFill()
    grad_path = NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(s*0.1, s*0.1, s*0.8, s*0.8))
    grad_path.fill()
    
    # Disk ring background
    r = s * 0.30
    ring = NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx-r, cy-r, r*2, r*2))
    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.15, 0.15, 0.25, 1.0).setFill()
    ring.fill()
    
    # Used portion (~35% pie)
    wedge = NSBezierPath.bezierPath()
    wedge.moveToPoint_(NSPoint(cx, cy))
    wedge.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
        NSPoint(cx, cy), r, 90, 90 - 360*0.35, True
    )
    wedge.closePath()
    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95, 0.30, 0.40, 1.0).setFill()
    wedge.fill()
    
    # Ring outline
    ring_outline = NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx-r, cy-r, r*2, r*2))
    NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.12).setStroke()
    ring_outline.setLineWidth_(max(2, s * 0.008))
    ring_outline.stroke()
    
    # Broom handle (diagonal)
    handle = NSBezierPath.bezierPath()
    handle.moveToPoint_(NSPoint(s*0.30, s*0.30))
    handle.lineToPoint_(NSPoint(s*0.68, s*0.68))
    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95, 0.30, 0.40, 0.75).setStroke()
    handle.setLineWidth_(max(4, s * 0.016))
    handle.setLineCapStyle_(1)
    handle.stroke()
    
    # Broom head (triangle-ish at top-left)
    head_size = s * 0.12
    hx, hy = s * 0.26, s * 0.26
    head = NSBezierPath.bezierPath()
    head.moveToPoint_(NSPoint(hx - head_size*0.5, hy))
    head.lineToPoint_(NSPoint(hx, hy - head_size*0.7))
    head.lineToPoint_(NSPoint(hx + head_size*0.3, hy + head_size*0.2))
    head.closePath()
    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95, 0.30, 0.40, 0.9).setFill()
    head.fill()
    
    # Sparkles
    sparkles = [
        (s*0.18, s*0.18, s*0.015),
        (s*0.15, s*0.24, s*0.010),
        (s*0.22, s*0.15, s*0.012),
        (s*0.13, s*0.21, s*0.008),
    ]
    for sx, sy, sr in sparkles:
        sparkle = NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(sx-sr, sy-sr, sr*2, sr*2))
        NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.6).setFill()
        sparkle.fill()
    
    NSGraphicsContext.restoreGraphicsState()
    return bmp


# Generate PNG at 1024x1024
print("Generating icon...")
bmp = draw_icon(1024)
png_data = bmp.representationUsingType_properties_(NSBitmapImageFileTypePNG, None)
png_path = os.path.join(ICON_DIR, "icon.png")
with open(png_path, "wb") as f:
    f.write(bytes(png_data))
print(f"  ✓ {png_path}")

# Create iconset for icns
iconset_dir = os.path.join(ICON_DIR, "broom-widget.iconset")
os.makedirs(iconset_dir, exist_ok=True)

import subprocess
for s in [16, 32, 64, 128, 256, 512, 1024]:
    dst = os.path.join(iconset_dir, f"icon_{s}x{s}.png")
    subprocess.run(["sips", "-z", str(s), str(s), png_path, "--out", dst],
                   capture_output=True)
    dst2x = os.path.join(iconset_dir, f"icon_{s}x{s}@2x.png")
    subprocess.run(["sips", "-z", str(s*2), str(s*2), png_path, "--out", dst2x],
                   capture_output=True)

# Convert to icns
icns_path = os.path.join(ICON_DIR, "broom-widget.icns")
result = subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
                        capture_output=True, text=True)
if result.returncode == 0:
    print(f"  ✓ {icns_path}")
else:
    print(f"  ✗ iconutil failed: {result.stderr}")
    # Copy PNG as fallback
    import shutil
    shutil.copy2(png_path, icns_path)

print("Done!")
