#!/bin/bash
# Install Apple's PingFang fonts from the macOS on-demand font asset catalog.
#
# Since macOS Sequoia, PingFang is not preinstalled: fresh CI runners only have
# the reserved UI copy (FontServices.framework/Resources/Reserved/PingFangUI.ttc),
# which CoreText reports as "PingFang SC" but which Pango/cairo refuse to use for
# document rendering — rsvg-convert then silently falls back to Hiragino Sans
# (Japanese glyph variants) for Chinese text in SVG figures. The CoreText
# on-demand download API is likewise a no-op because the reserved copy satisfies
# the descriptor match. So fetch the real font directly from Apple's asset CDN
# (the same channel macOS itself uses) and install it into ~/Library/Fonts.
#
# Usage: install_apple_fonts.sh

set -euo pipefail

for f in "$HOME/Library/Fonts/PingFang.ttc" /Library/Fonts/PingFang.ttc \
         /System/Library/Fonts/PingFang.ttc \
         /System/Library/AssetsV2/com_apple_MobileAsset_Font*/*.asset/AssetData/PingFang.ttc; do
    if [ -f "$f" ]; then
        echo "PingFang already installed: $f"
        exit 0
    fi
done

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# Font8 is the macOS 26 catalog generation; fall back to Font7 for older images.
url=""
for gen in Font8 Font7; do
    catalog="https://mesu.apple.com/assets/macos/com_apple_MobileAsset_${gen}/com_apple_MobileAsset_${gen}.xml"
    echo "Checking catalog $catalog"
    if ! curl -fsSL "$catalog" -o "$tmp/catalog.xml"; then
        continue
    fi
    url=$(python3 - "$tmp/catalog.xml" <<'EOF'
import plistlib, sys
cat = plistlib.load(open(sys.argv[1], "rb"))
for a in cat.get("Assets", []):
    if any(fi.get("FontFamilyName") == "PingFang SC" for fi in a.get("FontInfo4", [])):
        print(a["__BaseURL"] + a["__RelativePath"])
        break
EOF
)
    [ -n "$url" ] && break
done

if [ -z "$url" ]; then
    echo "ERROR: PingFang asset not found in any catalog" >&2
    exit 1
fi

echo "Downloading $url"
curl -fsSL "$url" -o "$tmp/pingfang.zip"
unzip -q "$tmp/pingfang.zip" -d "$tmp/asset"
mkdir -p "$HOME/Library/Fonts"
found=0
while IFS= read -r -d '' f; do
    cp "$f" "$HOME/Library/Fonts/"
    echo "Installed $(basename "$f") -> ~/Library/Fonts"
    found=1
done < <(find "$tmp/asset/AssetData" \( -name "*.ttc" -o -name "*.otf" -o -name "*.ttf" \) -print0)
if [ "$found" -eq 0 ]; then
    echo "ERROR: no font files found in downloaded asset" >&2
    exit 1
fi

# The PDF build renders SVGs with PANGOCAIRO_BACKEND=fontconfig, so verify the
# installed font through fontconfig (CoreText's view is irrelevant here, and
# whether fontd notices a new user font in time varies between runners).
if command -v fc-match >/dev/null 2>&1; then
    fc-cache -f >/dev/null 2>&1 || true
    match=$(fc-match "PingFang SC" 2>/dev/null || true)
    echo "fc-match PingFang SC -> $match"
    case "$match" in
        PingFang*) ;;
        *) echo "ERROR: fontconfig does not resolve PingFang SC after install" >&2
           exit 1;;
    esac
else
    echo "fc-match not available yet; the build's verify step will check the PDFs"
fi
echo "PingFang installed."
