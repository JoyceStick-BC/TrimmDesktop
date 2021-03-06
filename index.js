const {app, BrowserWindow, ipcMain} = require('electron');
const url = require('url');
const path = require('path');
const shell = require('electron').shell;

let win

function createWindow() {
   win = new BrowserWindow({width: 330, height: 600, titleBarStyle: 'hidden', frame: false, resizable: false});

   win.webContents.send('init-data', 'hello!');
   win.loadURL(url.format ({
      pathname: path.join(__dirname, 'redirect.html'),
      protocol: 'file:',
      slashes: true
  }));
}

app.on('ready', createWindow)
