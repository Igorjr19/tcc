import { app, BrowserWindow, ipcMain, dialog } from "electron";
import path from "node:path";
import { exec } from "child_process";
import util from "util";
import fs from "fs";
import started from "electron-squirrel-startup";

const execPromise = util.promisify(exec);

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (started) {
  app.quit();
}

const createWindow = () => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  // and load the index.html of the app.
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(
      path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`)
    );
  }

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.disableHardwareAcceleration();
app.on("ready", () => {
  console.log("App is ready, creating window...");
  try {
    createWindow();
  } catch (e) {
    console.error("Failed to create window:", e);
  }
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handler para abrir diálogo de seleção de pasta
ipcMain.handle("open-folder-picker", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"],
    title: "Selecione o diretório do projeto",
  });
  if (result.canceled || !result.filePaths || result.filePaths.length === 0) {
    return null;
  }
  return result.filePaths[0];
});

ipcMain.handle("analyze-project", async (_, projectPath: string) => {
  const jarPath = path.join(
    app.getAppPath(), // Aponta para /home/igor/projetos/tcc/autodep
    "../structural/target/structural-1.0-SNAPSHOT-jar-with-dependencies.jar"
  );
  const command = `java -jar "${jarPath}" "${projectPath}"`;

  try {
    const { stdout, stderr } = await execPromise(command);
    if (stderr) {
      console.error(`Analysis stderr: ${stderr}`);
      // Decide if stderr should be treated as an error
    }
    return stdout;
  } catch (error) {
    console.error(`Error executing JAR: ${error}`);
    throw new Error("Failed to analyze project");
  }
});

ipcMain.handle('export-results', async (_, data: string, format: string) => {
  try {
    const result = await dialog.showSaveDialog({
      title: 'Exportar Resultados',
      defaultPath: `analise-dependencias-${Date.now()}.${format}`,
      filters: [
        format === 'json' 
          ? { name: 'JSON Files', extensions: ['json'] }
          : { name: 'CSV Files', extensions: ['csv'] }
      ]
    });

    if (result.canceled || !result.filePath) {
      return null;
    }

    let content = data;
    if (format === 'csv') {
      // Convert JSON to CSV
      const jsonData = JSON.parse(data);
      content = convertToCSV(jsonData);
    }

    fs.writeFileSync(result.filePath, content, 'utf-8');
    return result.filePath;
  } catch (error) {
    console.error('Export error:', error);
    throw new Error('Failed to export results');
  }
});

interface ExportData {
  dependencies: Array<{
    groupId: string;
    artifactId: string;
    version: string;
    scope: string;
    usedByClasses: string[];
    usedImports: string[];
  }>;
}

function convertToCSV(data: ExportData): string {
  const lines: string[] = [];
  
  // Header line
  lines.push('GroupId,ArtifactId,Version,Scope,ClassesAcopladas,Status,Imports');
  
  // Data lines
  for (const dep of data.dependencies) {
    const row = [
      dep.groupId,
      dep.artifactId,
      dep.version || 'N/A',
      dep.scope,
      dep.usedByClasses.length.toString(),
      dep.usedByClasses.length > 0 ? 'Usado' : 'Não Usado',
      dep.usedImports.join('; ')
    ];
    lines.push(row.map(field => `"${field}"`).join(','));
  }
  
  return lines.join('\n');
}

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.
