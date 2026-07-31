const sharp = require('sharp');

// Cover background: deep indigo -> violet diagonal gradient, rasterized (CSS gradients not supported)
const cover = `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#14102E"/>
      <stop offset="55%" style="stop-color:#2A1668"/>
      <stop offset="100%" style="stop-color:#5B21B6"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#g)"/>
</svg>`;

sharp(Buffer.from(cover)).png().toFile('assets/cover-bg.png').then(() => console.log('assets ok'));
