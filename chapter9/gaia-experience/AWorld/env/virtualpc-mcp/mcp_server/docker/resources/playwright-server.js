const { chromium } = require("playwright");
// Read ws path from environment variable
const wsPath = process.env.WS_PATH || "default";
const port = process.env.PLAYWRIGHT_PORT || 37367;

(async () => {
  console.log("Starting Playwright server...");

  // Start the remote debugging server
  const browserServer = await chromium.launchServer({
    headless: false,
    port: port,
    wsPath: wsPath,
    args: [
      "--start-fullscreen",
      "--start-maximized",
      "--window-size=1280,1280",
      "--window-position=0,0",
      "--disable-infobars",
      "--no-default-browser-check",
      "--kiosk",
      "--disable-session-crashed-bubble",
      "--noerrdialogs",
      "--force-device-scale-factor=1.0",
      "--disable-features=DefaultViewportMetaTag",
      "--force-device-width=1280",
    ],
  });

  console.log(`Playwright server running: ${browserServer.wsEndpoint()}`);

  // Keep the process running
  process.on("SIGINT", async () => {
    console.log("Shutting down Playwright server...");
    // await browser.close();
    await browserServer.close();
    process.exit(0);
  });
})();
