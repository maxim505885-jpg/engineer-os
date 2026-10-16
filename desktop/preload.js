const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('engineerDesktop',Object.freeze({isDesktop:true,info:()=>ipcRenderer.invoke('engineer:info'),hideWindow:()=>ipcRenderer.invoke('engineer:hideWindow'),openProjectFolder:()=>ipcRenderer.invoke('engineer:openProjectFolder'),openServerLog:()=>ipcRenderer.invoke('engineer:openServerLog')}));
