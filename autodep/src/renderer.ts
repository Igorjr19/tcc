/**
 * This file will automatically be loaded by vite and run in the "renderer" context.
 * To learn more about the differences between the "main" and the "renderer" context in
 * Electron, visit:
 *
 * https://electronjs.org/docs/tutorial/process-model
 *
 * By default, Node.js integration in this file is disabled. When enabling Node.js integration
 * in a renderer process, please be aware of potential security implications. You can read
 * more about security risks here:
 *
 * https://electronjs.org/docs/tutorial/security
 *
 * To enable Node.js integration in this file, open up `main.ts` and enable the `nodeIntegration`
 * flag:
 *
 * ```
 *  // Create the browser window.
 *  mainWindow = new BrowserWindow({
 *    width: 800,
 *    height: 600,
 *    webPreferences: {
 *      nodeIntegration: true
 *    }
 *  });
 * ```
 */

import './index.css';

declare global {
  interface Window {
    electronAPI: {
      openFolderPicker: () => Promise<string | null>;
      analyzeProject: (projectPath: string) => Promise<string>;
    };
  }
}

const appRoot = document.createElement('div');
appRoot.innerHTML = `
  <h1>AutoDep</h1>
  <p>Carregue o seu projeto para começar.</p>
  <div style="display:flex;gap:8px;align-items:center;">
    <button id="selectBtn">Selecionar projeto</button>
    <span id="path">Nenhum projeto selecionado</span>
  </div>
  <div style="margin-top:1rem;">
    <button id="loadBtn" disabled>Carregar projeto</button>
  </div>
`;

document.body.innerHTML = '';
document.body.appendChild(appRoot);

const selectBtn = document.getElementById('selectBtn') as HTMLButtonElement;
const pathSpan = document.getElementById('path') as HTMLSpanElement;
const loadBtn = document.getElementById('loadBtn') as HTMLButtonElement;

let selectedPath: string | null = null;

selectBtn.addEventListener('click', async () => {
  const result = await window.electronAPI.openFolderPicker();
  if (result) {
    selectedPath = result;
    pathSpan.textContent = result;
    loadBtn.disabled = false;
  } else {
    selectedPath = null;
    pathSpan.textContent = 'Nenhum projeto selecionado';
    loadBtn.disabled = true;
  }
});

loadBtn.addEventListener('click', () => {
  if (!selectedPath) return;
  console.log('Analyzing project at:', selectedPath);
  void (async () => {
    try {
      const analysisResult = await window.electronAPI.analyzeProject(selectedPath);
      console.log('Analysis result:', analysisResult);
      
      // Create a new view for the results
      const resultsDiv = document.createElement('div');
      resultsDiv.innerHTML = `
        <h2>Analysis Results</h2>
        <pre>${analysisResult}</pre>
      `;
      
      // Replace the current view with the results view
      document.body.innerHTML = '';
      document.body.appendChild(resultsDiv);

    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Failed to analyze project.');
    }
  })();
});
