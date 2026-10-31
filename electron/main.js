const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');

function createWindow() {
  dialog.showMessageBox({
    type: 'warning',
    title: 'LEGALLY RESTRICTED — READ BEFORE OPENING',
    message: 'PROPRIETARY RESTRICTED LICENSE\n\nUnauthorized use, redistribution, editing, or modification is PROHIBITED. All rights reserved to Authenticated, Inc. — Trey A. Smith.',
    buttons: ['I Agree — Launch'],
    defaultId: 0
  }).then(() => {
    const win = new BrowserWindow({ width: 1200, height: 800, webPreferences: { nodeIntegration: false } });
    win.loadURL('http://localhost:5000/');
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
