const { app, BrowserWindow, globalShortcut, session } = require('electron');
const path = require('path');

app.whenReady().then(() => {
  const win = new BrowserWindow({
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    width: 1200,
    height: 800,
    show: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
    },
  });

  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.youtube.com https://*.ytimg.com https://*.google.com https://*.ggpht.com https://fonts.googleapis.com https://fonts.gstatic.com data:; media-src 'self' https: data: blob:; img-src 'self' https: data:; connect-src 'self' https:;"
        ]
      }
    });
  });

  win.loadFile(path.join(__dirname, 'src', 'index.html'));

  win.setAlwaysOnTop(true, 'screen-saver');

  win.on('closed', () => { win = null; });
});

app.on('window-all-closed', () => { app.quit(); });
