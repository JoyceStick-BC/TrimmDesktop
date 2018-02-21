const {app, BrowserWindow} = require('electron')
const url = require('url')
const path = require('path')
const shell = require('electron').shell

let win

function createWindow() {
   win = new BrowserWindow({width: 800, height: 600, titleBarStyle: 'hidden', frame: false});
   win.setMenu(null);
   win.loadURL(url.format ({
      pathname: path.join(__dirname, 'index.html'),
      protocol: 'file:',
      slashes: true
   }))
}

app.on('ready', createWindow)
