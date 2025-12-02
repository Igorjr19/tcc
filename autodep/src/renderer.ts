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

interface ClassInfo {
  className: string;
  simpleName: string;
  packageName: string;
  filePath: string;
  isInterface: boolean;
  isAbstract: boolean;
  methodCount: number;
  fieldCount: number;
  dependsOn: string[];
  dependedByClasses: string[];
  couplingOut: number;
  couplingIn: number;
  totalCoupling: number;
  instability: number;
}

interface AnalysisResult {
  projectName: string;
  projectPath: string;
  projectGroupId: string;
  totalClasses: number;
  averageCoupling: number;
  maxCoupling: number;
  highlyCoupledClasses: number;
  classes: ClassInfo[];
}

declare global {
  interface Window {
    electronAPI: {
      openFolderPicker: () => Promise<string | null>;
      analyzeProject: (projectPath: string) => Promise<string>;
      exportResults: (data: string, format: string) => Promise<string | null>;
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
  
  // Show loading state
  loadBtn.disabled = true;
  loadBtn.textContent = 'Analisando...';
  
  void (async () => {
    try {
      const analysisResultStr = await window.electronAPI.analyzeProject(selectedPath);
      const analysisResult = JSON.parse(analysisResultStr);
      
      displayResults(analysisResult);

    } catch (error) {
      console.error('Analysis failed:', error);
      loadBtn.disabled = false;
      loadBtn.textContent = 'Carregar projeto';
      alert('Falha ao analisar projeto: ' + (error as Error).message);
    }
  })();
});

function displayResults(result: AnalysisResult) {
  document.body.innerHTML = '';
  
  const container = document.createElement('div');
  container.style.padding = '20px';
  container.style.maxWidth = '1200px';
  container.style.margin = '0 auto';
  
  // Header
  const header = document.createElement('div');
  header.innerHTML = `
    <h1>Análise de Acoplamento Estrutural</h1>
    <h2>${result.projectName || 'Projeto'}</h2>
    <p style="color: #666;">${result.projectPath}</p>
    <p style="color: #999; font-size: 12px; margin-top: 5px;">
      Package Base: <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">${result.projectGroupId || 'N/A'}</code>
    </p>
  `;
  container.appendChild(header);
  
  // Summary cards
  const summaryDiv = document.createElement('div');
  summaryDiv.style.display = 'grid';
  summaryDiv.style.gridTemplateColumns = 'repeat(auto-fit, minmax(200px, 1fr))';
  summaryDiv.style.gap = '15px';
  summaryDiv.style.margin = '20px 0';
  
  const cards = [
    { label: 'Total de Classes', value: result.totalClasses, color: '#2196F3' },
    { label: 'Acoplamento Médio', value: result.averageCoupling.toFixed(2), color: '#4CAF50' },
    { label: 'Acoplamento Máximo', value: result.maxCoupling, color: '#FF9800' },
    { label: 'Classes Altamente Acopladas', value: result.highlyCoupledClasses, color: '#f44336' }
  ];
  
  cards.forEach(card => {
    const cardDiv = document.createElement('div');
    cardDiv.style.padding = '15px';
    cardDiv.style.backgroundColor = '#f5f5f5';
    cardDiv.style.borderRadius = '8px';
    cardDiv.style.borderLeft = `4px solid ${card.color}`;
    cardDiv.innerHTML = `
      <div style="font-size: 12px; color: #666; margin-bottom: 5px;">${card.label}</div>
      <div style="font-size: 24px; font-weight: bold; color: ${card.color};">${card.value}</div>
    `;
    summaryDiv.appendChild(cardDiv);
  });
  
  container.appendChild(summaryDiv);
  
  // Tabs
  const tabsContainer = document.createElement('div');
  tabsContainer.style.marginTop = '30px';
  
  const tabButtons = document.createElement('div');
  tabButtons.style.display = 'flex';
  tabButtons.style.gap = '10px';
  tabButtons.style.borderBottom = '2px solid #ddd';
  tabButtons.style.marginBottom = '20px';
  
  const tabs = [
    { id: 'all', label: 'Todas as Classes' },
    { id: 'coupling', label: 'Ranking de Acoplamento' },
    { id: 'highly-coupled', label: 'Classes Altamente Acopladas' }
  ];
  
  const tabContents: { [key: string]: HTMLElement } = {};
  
  tabs.forEach((tab, index) => {
    const btn = document.createElement('button');
    btn.textContent = tab.label;
    btn.style.padding = '10px 20px';
    btn.style.border = 'none';
    btn.style.background = 'none';
    btn.style.cursor = 'pointer';
    btn.style.borderBottom = index === 0 ? '2px solid #2196F3' : '2px solid transparent';
    btn.style.fontWeight = index === 0 ? 'bold' : 'normal';
    
    btn.addEventListener('click', () => {
      // Update button styles
      tabButtons.querySelectorAll('button').forEach(b => {
        (b as HTMLElement).style.borderBottom = '2px solid transparent';
        (b as HTMLElement).style.fontWeight = 'normal';
      });
      btn.style.borderBottom = '2px solid #2196F3';
      btn.style.fontWeight = 'bold';
      
      // Show corresponding content
      Object.values(tabContents).forEach(content => content.style.display = 'none');
      tabContents[tab.id].style.display = 'block';
    });
    
    tabButtons.appendChild(btn);
  });
  
  tabsContainer.appendChild(tabButtons);
  
  // Tab contents
  const contentContainer = document.createElement('div');
  
  // All classes
  const allContent = createClassTable(result.classes);
  allContent.style.display = 'block';
  tabContents['all'] = allContent;
  
  // Coupling ranking
  const couplingContent = createCouplingRanking(result.classes);
  couplingContent.style.display = 'none';
  tabContents['coupling'] = couplingContent;
  
  // Highly coupled classes (top 20% or minimum coupling > 5)
  const highlyCoupled = result.classes.filter(c => c.totalCoupling >= 5).slice(0, Math.ceil(result.totalClasses * 0.2));
  const highlyContent = createClassTable(highlyCoupled);
  highlyContent.style.display = 'none';
  tabContents['highly-coupled'] = highlyContent;
  
  Object.values(tabContents).forEach(content => contentContainer.appendChild(content));
  
  tabsContainer.appendChild(contentContainer);
  container.appendChild(tabsContainer);
  
  // Export and navigation buttons
  const buttonContainer = document.createElement('div');
  buttonContainer.style.marginTop = '30px';
  buttonContainer.style.display = 'flex';
  buttonContainer.style.gap = '10px';
  buttonContainer.style.flexWrap = 'wrap';
  
  const backBtn = document.createElement('button');
  backBtn.textContent = '← Analisar outro projeto';
  backBtn.style.padding = '10px 20px';
  backBtn.addEventListener('click', () => window.location.reload());
  
  const exportJsonBtn = document.createElement('button');
  exportJsonBtn.textContent = '📄 Exportar JSON';
  exportJsonBtn.style.padding = '10px 20px';
  exportJsonBtn.style.backgroundColor = '#2196F3';
  exportJsonBtn.style.color = 'white';
  exportJsonBtn.style.border = 'none';
  exportJsonBtn.style.borderRadius = '4px';
  exportJsonBtn.style.cursor = 'pointer';
  exportJsonBtn.addEventListener('click', () => exportData(result, 'json'));
  
  const exportCsvBtn = document.createElement('button');
  exportCsvBtn.textContent = '📊 Exportar CSV';
  exportCsvBtn.style.padding = '10px 20px';
  exportCsvBtn.style.backgroundColor = '#4CAF50';
  exportCsvBtn.style.color = 'white';
  exportCsvBtn.style.border = 'none';
  exportCsvBtn.style.borderRadius = '4px';
  exportCsvBtn.style.cursor = 'pointer';
  exportCsvBtn.addEventListener('click', () => exportData(result, 'csv'));
  
  buttonContainer.appendChild(backBtn);
  buttonContainer.appendChild(exportJsonBtn);
  buttonContainer.appendChild(exportCsvBtn);
  container.appendChild(buttonContainer);
  
  document.body.appendChild(container);
}

async function exportData(result: AnalysisResult, format: string) {
  try {
    const data = JSON.stringify(result, null, 2);
    const filePath = await window.electronAPI.exportResults(data, format);
    
    if (filePath) {
      alert(`Arquivo exportado com sucesso em:\\n${filePath}`);
    }
  } catch (error) {
    console.error('Export failed:', error);
    alert('Falha ao exportar: ' + (error as Error).message);
  }
}

function createClassTable(classes: ClassInfo[]) {
  const div = document.createElement('div');
  
  if (classes.length === 0) {
    div.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">Nenhuma classe encontrada.</p>';
    return div;
  }
  
  const table = document.createElement('table');
  table.style.width = '100%';
  table.style.borderCollapse = 'collapse';
  table.innerHTML = `
    <thead>
      <tr style="background-color: #f5f5f5; text-align: left;">
        <th style="padding: 12px; border-bottom: 2px solid #ddd;">Classe</th>
        <th style="padding: 12px; border-bottom: 2px solid #ddd;">Pacote</th>
        <th style="padding: 12px; border-bottom: 2px solid #ddd; text-align: center;">Tipo</th>
        <th style="padding: 12px; border-bottom: 2px solid #ddd; text-align: center;">CBO Out</th>
        <th style="padding: 12px; border-bottom: 2px solid #ddd; text-align: center;">CBO In</th>
        <th style="padding: 12px; border-bottom: 2px solid #ddd; text-align: center;">Total</th>
      </tr>
    </thead>
    <tbody>
      ${classes.map(cls => {
        const couplingOut = cls.couplingOut || 0;
        const couplingIn = cls.couplingIn || 0;
        const totalCoupling = couplingOut + couplingIn;
        const instability = (couplingOut + couplingIn) === 0 ? 0 : couplingOut / (couplingOut + couplingIn);
        
        const typeLabel = cls.isInterface ? 'Interface' : cls.isAbstract ? 'Abstrata' : 'Classe';
        const instabilityColor = instability > 0.7 ? '#f44336' : instability > 0.4 ? '#FF9800' : '#4CAF50';
        const couplingColor = totalCoupling > 10 ? '#f44336' : totalCoupling > 5 ? '#FF9800' : '#4CAF50';
        
        return `
        <tr style="border-bottom: 1px solid #eee;" title="${cls.className}">
          <td style="padding: 10px;"><strong>${cls.simpleName}</strong></td>
          <td style="padding: 10px; color: #666; font-size: 12px;">${cls.packageName}</td>
          <td style="padding: 10px; text-align: center;">
            <span style="padding: 3px 6px; border-radius: 3px; font-size: 11px; background-color: #e3f2fd; color: #1976d2;">
              ${typeLabel}
            </span>
          </td>
          <td style="padding: 10px; text-align: center;">${couplingOut}</td>
          <td style="padding: 10px; text-align: center;">${couplingIn}</td>
          <td style="padding: 10px; text-align: center;">
            <span style="padding: 4px 8px; border-radius: 4px; font-weight: bold; background-color: ${couplingColor}20; color: ${couplingColor};">
              ${totalCoupling}
            </span>
          </td>
        </tr>
      `;
      }).join('')}
    </tbody>
  `;
  
  div.appendChild(table);
  return div;
}

function createCouplingRanking(classes: ClassInfo[]) {
  const div = document.createElement('div');
  
  const sortedClasses = [...classes]
    .map(cls => ({
      ...cls,
      totalCoupling: (cls.couplingOut || 0) + (cls.couplingIn || 0)
    }))
    .sort((a, b) => b.totalCoupling - a.totalCoupling)
    .slice(0, 20); // Top 20 most coupled classes
  
  if (sortedClasses.length === 0) {
    div.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">Nenhuma classe encontrada.</p>';
    return div;
  }
  
  sortedClasses.forEach((cls, index) => {
    const card = document.createElement('div');
    card.style.padding = '15px';
    card.style.marginBottom = '10px';
    card.style.backgroundColor = '#f9f9f9';
    card.style.borderRadius = '8px';
    card.style.borderLeft = '4px solid ' + getColorForRank(index);
    
    const couplingOut = cls.couplingOut || 0;
    const couplingIn = cls.couplingIn || 0;
    const totalCoupling = cls.totalCoupling || (couplingOut + couplingIn);
    const instability = (couplingOut + couplingIn) === 0 ? 0 : couplingOut / (couplingOut + couplingIn);
    const typeLabel = cls.isInterface ? '(Interface)' : cls.isAbstract ? '(Abstrata)' : '';
    
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex: 1;">
          <div style="font-size: 18px; font-weight: bold; color: #333;">
            #${index + 1} ${cls.simpleName} ${typeLabel}
          </div>
          <div style="font-size: 12px; color: #666; margin-top: 5px;">
            ${cls.packageName}
          </div>
          <div style="font-size: 11px; color: #999; margin-top: 3px;">
            Métodos: ${cls.methodCount || 0} | Campos: ${cls.fieldCount || 0}
          </div>
        </div>
        <div style="text-align: right; margin-left: 20px;">
          <div style="font-size: 24px; font-weight: bold; color: ${getColorForRank(index)};">
            ${totalCoupling}
          </div>
          <div style="font-size: 12px; color: #666;">
            acoplamento total
          </div>
          <div style="font-size: 11px; color: #999; margin-top: 3px;">
            Out: ${couplingOut} | In: ${couplingIn}
          </div>
        </div>
      </div>
      ${(cls.dependsOn && cls.dependsOn.length > 0) ? `
        <details style="margin-top: 10px;">
          <summary style="cursor: pointer; color: #666; font-size: 12px;">Ver dependências (${cls.dependsOn.length})</summary>
          <ul style="margin-top: 10px; font-size: 12px; color: #666;">
            ${cls.dependsOn.slice(0, 10).map((dep: string) => `<li>${dep}</li>`).join('')}
            ${cls.dependsOn.length > 10 ? `<li><em>...e mais ${cls.dependsOn.length - 10}</em></li>` : ''}
          </ul>
        </details>
      ` : ''}
      ${(cls.dependedByClasses && cls.dependedByClasses.length > 0) ? `
        <details style="margin-top: 10px;">
          <summary style="cursor: pointer; color: #666; font-size: 12px;">Classes que dependem desta (${cls.dependedByClasses.length})</summary>
          <ul style="margin-top: 10px; font-size: 12px; color: #666;">
            ${cls.dependedByClasses.slice(0, 10).map((dep: string) => `<li>${dep}</li>`).join('')}
            ${cls.dependedByClasses.length > 10 ? `<li><em>...e mais ${cls.dependedByClasses.length - 10}</em></li>` : ''}
          </ul>
        </details>
      ` : ''}
    `;
    
    div.appendChild(card);
  });
  
  return div;
}

function getColorForRank(index: number): string {
  if (index === 0) return '#f44336';
  if (index === 1) return '#FF9800';
  if (index === 2) return '#FFC107';
  return '#2196F3';
}
