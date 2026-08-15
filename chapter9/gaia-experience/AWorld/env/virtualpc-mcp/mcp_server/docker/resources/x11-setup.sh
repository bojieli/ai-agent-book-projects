#!/bin/bash

# Make sure DISPLAY is set
if [ -z "$DISPLAY" ]; then
  export DISPLAY=:99
fi

# Set background to black to make black bars less obvious
xsetroot -solid "#000000"

# Force X11 to use the exact screen dimensions without any offsets
xrandr --output default --mode 1280x1280 --pos 0x0

# Set proper DPI settings for the display
echo "Xft.dpi: 96" | xrdb -merge
echo "Xft.antialias: 1" | xrdb -merge
echo "Xft.hinting: 1" | xrdb -merge
echo "Xft.hintstyle: hintfull" | xrdb -merge
echo "Xft.rgba: rgb" | xrdb -merge

# Disable any screen savers or power management
xset s off
xset -dpms
xset s noblank

# Ensure consistent scaling
xrandr --dpi 96

echo "X11 environment configured for optimal display"