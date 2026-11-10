/* Rasterize the supplied official SVG; no emblem paths are recreated or recolored. */
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('@playwright/test');

const assets = path.resolve(__dirname, '../src/public/assets');
const source = fs.readFileSync(path.join(assets, 'img/branding/logos/eagle-gold.svg'));

async function main() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage();
    const images = await page.evaluate(
      async (svg) => {
        const emblem = new Image();
        emblem.src = svg;
        await emblem.decode();
        const draw = (size, alert = false) => {
          const canvas = document.createElement('canvas');
          canvas.width = size;
          canvas.height = size;
          const context = canvas.getContext('2d');
          context.scale(size / 70, size / 70);
          context.fillStyle = '#002623';
          context.beginPath();
          context.arc(35, 35, 35, 0, Math.PI * 2);
          context.fill();
          const width = 54;
          const height = (width * emblem.naturalHeight) / emblem.naturalWidth;
          context.drawImage(emblem, 8, (70 - height) / 2, width, height);
          if (alert) {
            // Preserve the notification badge footprint within the approved palette.
            context.fillStyle = '#6b1f2a';
            context.beginPath();
            context.arc(52, 18, 18, 0, Math.PI * 2);
            context.fill();
          }
          return canvas.toDataURL('image/png').split(',')[1];
        };
        return {
          normal: draw(70),
          alert: draw(70, true),
          ico: [16, 32, 48, 64].map((size) => ({ size, png: draw(size) })),
        };
      },
      `data:image/svg+xml;base64,${source.toString('base64')}`,
    );
    fs.writeFileSync(path.join(assets, 'favicon.png'), Buffer.from(images.normal, 'base64'));
    fs.writeFileSync(path.join(assets, 'favicon-alert.png'), Buffer.from(images.alert, 'base64'));

    // ICO supports PNG-compressed images; preserve alpha at each native icon size.
    const header = Buffer.alloc(6 + images.ico.length * 16);
    header.writeUInt16LE(1, 2);
    header.writeUInt16LE(images.ico.length, 4);
    let offset = header.length;
    const payloads = images.ico.map(({ size, png }, index) => {
      const payload = Buffer.from(png, 'base64');
      const entry = 6 + index * 16;
      header[entry] = size;
      header[entry + 1] = size;
      header.writeUInt16LE(1, entry + 4);
      header.writeUInt16LE(32, entry + 6);
      header.writeUInt32LE(payload.length, entry + 8);
      header.writeUInt32LE(offset, entry + 12);
      offset += payload.length;
      return payload;
    });
    fs.writeFileSync(path.join(assets, 'favicon.ico'), Buffer.concat([header, ...payloads]));
    console.log('Generated official-eagle normal, alert and multi-size ICO favicons');
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
