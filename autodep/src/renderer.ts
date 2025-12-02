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
import { Network } from 'vis-network';

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
    <h1>Análise de CBO (Coupling Between Objects)</h1>
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
    { label: 'CBO Médio', value: result.averageCoupling.toFixed(2), color: '#4CAF50' },
    { label: 'CBO Máximo', value: result.maxCoupling, color: '#FF9800' },
    { label: 'Classes Alto CBO', value: result.highlyCoupledClasses, color: '#f44336' }
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
    { id: 'graph', label: 'Grafo de Dependências' },
    { id: 'coupling', label: 'Ranking CBO' },
    { id: 'highly-coupled', label: 'Classes Alto CBO' }
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
      
      // Render graph when tab is shown
      if (tab.id === 'graph' && (tabContents[tab.id] as any)._renderGraph) {
        setTimeout(() => (tabContents[tab.id] as any)._renderGraph(), 50);
      }
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
  
  // Dependency graph
  const { container: graphContent, renderGraph } = createDependencyGraph(result.classes);
  graphContent.style.display = 'none';
  tabContents['graph'] = graphContent;
  
  // Store render function for later use
  (graphContent as any)._renderGraph = renderGraph;
  
  // Coupling ranking
  const couplingContent = createCouplingRanking(result.classes);
  couplingContent.style.display = 'none';
  tabContents['coupling'] = couplingContent;
  
  // Highly coupled classes (top 20% or minimum coupling > 5)
  const highlyCoupled = result.classes
    .filter(c => {
      const total = (c.couplingOut || 0) + (c.couplingIn || 0);
      return total >= 5;
    })
    .sort((a, b) => {
      const totalA = (a.couplingOut || 0) + (a.couplingIn || 0);
      const totalB = (b.couplingOut || 0) + (b.couplingIn || 0);
      return totalB - totalA;
    })
    .slice(0, Math.max(Math.ceil(result.totalClasses * 0.2), 10));
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

function createDependencyGraph(classes: ClassInfo[]) {
  const container = document.createElement('div');
  container.style.padding = '20px';
  
  // Controls
  const controls = document.createElement('div');
  controls.style.marginBottom = '15px';
  controls.style.display = 'flex';
  controls.style.gap = '15px';
  controls.style.flexWrap = 'wrap';
  controls.style.alignItems = 'center';
  
  // Filter by minimum coupling
  const couplingLabel = document.createElement('label');
  couplingLabel.textContent = 'CBO mínimo: ';
  couplingLabel.style.fontSize = '14px';
  
  const couplingSlider = document.createElement('input');
  couplingSlider.type = 'range';
  couplingSlider.min = '0';
  couplingSlider.max = '20';
  couplingSlider.value = '0';
  couplingSlider.style.width = '150px';
  
  const couplingValue = document.createElement('span');
  couplingValue.textContent = '0';
  couplingValue.style.marginLeft = '5px';
  couplingValue.style.fontWeight = 'bold';
  
  couplingSlider.addEventListener('input', () => {
    couplingValue.textContent = couplingSlider.value;
    updateGraph();
  });
  
  couplingLabel.appendChild(couplingSlider);
  couplingLabel.appendChild(couplingValue);
  
  // Filter by package
  const packageLabel = document.createElement('label');
  packageLabel.textContent = 'Filtrar por pacote: ';
  packageLabel.style.fontSize = '14px';
  
  const packageSelect = document.createElement('select');
  packageSelect.style.padding = '5px';
  
  // Get unique packages
  const packages = [...new Set(classes.map(c => c.packageName))].sort();
  packageSelect.innerHTML = '<option value="">Todos os pacotes</option>' + 
    packages.map(pkg => `<option value="${pkg}">${pkg}</option>`).join('');
  
  packageSelect.addEventListener('change', updateGraph);
  packageLabel.appendChild(packageSelect);
  
  // Show interfaces/abstract checkbox
  const typesLabel = document.createElement('label');
  typesLabel.style.fontSize = '14px';
  typesLabel.style.display = 'flex';
  typesLabel.style.alignItems = 'center';
  typesLabel.style.gap = '5px';
  
  const showInterfacesCheck = document.createElement('input');
  showInterfacesCheck.type = 'checkbox';
  showInterfacesCheck.checked = true;
  showInterfacesCheck.addEventListener('change', updateGraph);
  
  typesLabel.appendChild(showInterfacesCheck);
  typesLabel.appendChild(document.createTextNode('Mostrar Interfaces/Abstratas'));
  
  controls.appendChild(couplingLabel);
  controls.appendChild(packageLabel);
  controls.appendChild(typesLabel);
  container.appendChild(controls);
  
  // Graph container
  const graphDiv = document.createElement('div');
  graphDiv.id = 'dependency-graph';
  graphDiv.style.width = '100%';
  graphDiv.style.height = '600px';
  graphDiv.style.border = '1px solid #ddd';
  graphDiv.style.borderRadius = '8px';
  graphDiv.style.backgroundColor = '#fafafa';
  container.appendChild(graphDiv);
  
  // Legend
  const legend = document.createElement('div');
  legend.style.marginTop = '15px';
  legend.style.padding = '15px';
  legend.style.backgroundColor = '#fff';
  legend.style.border = '1px solid #ddd';
  legend.style.borderRadius = '8px';
  legend.style.display = 'grid';
  legend.style.gridTemplateColumns = 'repeat(auto-fit, minmax(200px, 1fr))';
  legend.style.gap = '15px';
  
  legend.innerHTML = `
    <div>
      <div style="font-weight: bold; margin-bottom: 8px; color: #333;">Cores (CBO)</div>
      <div style="display: flex; flex-direction: column; gap: 5px; font-size: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 20px; height: 20px; background: #f44336; border-radius: 3px;"></div>
          <span>Alto (&gt; 10)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 20px; height: 20px; background: #FF9800; border-radius: 3px;"></div>
          <span>Médio-Alto (6-10)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 20px; height: 20px; background: #FFC107; border-radius: 3px;"></div>
          <span>Médio (3-5)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 20px; height: 20px; background: #4CAF50; border-radius: 3px;"></div>
          <span>Baixo (0-2)</span>
        </div>
      </div>
    </div>
    <div>
      <div style="font-weight: bold; margin-bottom: 8px; color: #333;">Formas (Tipo)</div>
      <div style="display: flex; flex-direction: column; gap: 5px; font-size: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 20px; height: 20px; background: #999; border-radius: 0;"></div>
          <span>Classe Concreta</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 20px; height: 20px; background: #999; border-radius: 50%;"></div>
          <span>Interface</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 20px; height: 20px; background: #999; transform: rotate(45deg);"></div>
          <span>Classe Abstrata</span>
        </div>
      </div>
    </div>
    <div>
      <div style="font-weight: bold; margin-bottom: 8px; color: #333;">Interação</div>
      <div style="display: flex; flex-direction: column; gap: 5px; font-size: 12px; color: #666;">
        <div>• Clique em um nó para destacar conexões</div>
        <div>• Arraste para mover o grafo</div>
        <div>• Scroll para zoom</div>
        <div>• Passe o mouse para ver detalhes</div>
      </div>
    </div>
  `;
  container.appendChild(legend);
  
  // Stats
  const stats = document.createElement('div');
  stats.style.marginTop = '15px';
  stats.style.padding = '10px';
  stats.style.backgroundColor = '#f5f5f5';
  stats.style.borderRadius = '4px';
  stats.style.fontSize = '12px';
  stats.style.color = '#666';
  container.appendChild(stats);
  
  let network: Network | null = null;
  
  function updateGraph() {
    const minCoupling = parseInt(couplingSlider.value);
    const selectedPackage = packageSelect.value;
    const showInterfaces = showInterfacesCheck.checked;
    
    // Filter classes
    const filteredClasses = classes.filter(cls => {
      const couplingOut = cls.couplingOut || 0;
      const couplingIn = cls.couplingIn || 0;
      const totalCoupling = couplingOut + couplingIn;
      
      if (totalCoupling < minCoupling) return false;
      if (selectedPackage && cls.packageName !== selectedPackage) return false;
      if (!showInterfaces && (cls.isInterface || cls.isAbstract)) return false;
      
      return true;
    });
    
    // Build nodes
    const nodes = filteredClasses.map(cls => {
      const couplingOut = cls.couplingOut || 0;
      const couplingIn = cls.couplingIn || 0;
      const totalCoupling = couplingOut + couplingIn;
      
      // Color based on coupling intensity
      let color;
      if (totalCoupling > 10) color = '#f44336';
      else if (totalCoupling > 5) color = '#FF9800';
      else if (totalCoupling > 2) color = '#FFC107';
      else color = '#4CAF50';
      
      // Shape based on type
      let shape = 'box';
      if (cls.isInterface) shape = 'ellipse';
      else if (cls.isAbstract) shape = 'diamond';
      
      return {
        id: cls.className,
        label: cls.simpleName,
        title: `${cls.className}\nCBO Out: ${couplingOut} | CBO In: ${couplingIn}\nTotal: ${totalCoupling}`,
        color: { background: color, border: color },
        shape: shape,
        font: { size: 14, color: '#000', face: 'arial' }
      };
    });
    
    // Build edges
    const classNames = new Set(filteredClasses.map(c => c.className));
    const edges: Array<{from: string; to: string; arrows: string; color: {color: string; opacity: number}; width: number}> = [];
    
    filteredClasses.forEach(cls => {
      if (cls.dependsOn && cls.dependsOn.length > 0) {
        cls.dependsOn.forEach(dep => {
          // Only show edges between filtered classes
          if (classNames.has(dep)) {
            edges.push({
              from: cls.className,
              to: dep,
              arrows: 'to',
              color: { color: '#999', opacity: 0.5 },
              width: 1
            });
          }
        });
      }
    });
    
    // Update stats
    stats.innerHTML = `
      <strong>Estatísticas do Grafo:</strong> 
      ${nodes.length} classes | ${edges.length} dependências | CBO médio: ${(nodes.reduce((sum, n) => sum + (classes.find(c => c.className === n.id)?.couplingOut || 0) + (classes.find(c => c.className === n.id)?.couplingIn || 0), 0) / nodes.length).toFixed(2)}
    `;
    
    // Create/update network
    const data = { nodes, edges };
    const options = {
      layout: {
        improvedLayout: false,
        hierarchical: {
          enabled: false
        }
      },
      physics: {
        enabled: true,
        stabilization: {
          enabled: true,
          iterations: 100,
          fit: true
        },
        barnesHut: {
          gravitationalConstant: -3000,
          centralGravity: 0.1,
          springLength: 120,
          springConstant: 0.05,
          damping: 0.99,
          avoidOverlap: 0.3
        },
        maxVelocity: 15,
        minVelocity: 1,
        timestep: 0.35,
        adaptiveTimestep: true
      },
      nodes: {
        borderWidth: 2,
        borderWidthSelected: 4,
        size: 25,
        font: {
          size: 14,
          color: '#000',
          face: 'arial'
        }
      },
      edges: {
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.5
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true
      }
    };
    
    if (network) {
      network.setData(data);
    } else {
      network = new Network(graphDiv, data, options);
      
      // Click event to highlight connections
      network.on('selectNode', (params) => {
        if (params.nodes.length > 0 && network) {
          const selectedId = params.nodes[0];
          const connectedNodes = network.getConnectedNodes(selectedId);
          const nodesToSelect = [selectedId];
          if (Array.isArray(connectedNodes)) {
            nodesToSelect.push(...connectedNodes as string[]);
          }
          network.selectNodes(nodesToSelect);
        }
      });
    }
  }
  
  // Return container and render function
  return { 
    container, 
    renderGraph: updateGraph 
  };
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
        <th style="padding: 12px; border-bottom: 2px solid #ddd; text-align: center;">CBO Total</th>
      </tr>
    </thead>
    <tbody>
      ${classes.map(cls => {
        const couplingOut = cls.couplingOut || 0;
        const couplingIn = cls.couplingIn || 0;
        const totalCoupling = couplingOut + couplingIn;
        
        const typeLabel = cls.isInterface ? 'Interface' : cls.isAbstract ? 'Abstrata' : 'Classe';
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
            CBO total
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
