// Preload script: expõe API segura ao renderer via contextBridge
// https://www.electronjs.org/docs/latest/tutorial/ipc
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
	openFolderPicker: (): Promise<string | null> => ipcRenderer.invoke('open-folder-picker'),
	analyzeProject: (projectPath: string): Promise<string> =>
		ipcRenderer.invoke('analyze-project', projectPath),
});
