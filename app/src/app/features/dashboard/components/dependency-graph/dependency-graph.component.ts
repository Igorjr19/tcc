import {
  Component,
  input,
  output,
  signal,
  effect,
  viewChild,
  ElementRef,
  afterNextRender,
  OnDestroy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import cytoscape from 'cytoscape';
import { NodeInfo } from '../../../../core/models/NodeInfo';
import { EdgeInfo } from '../../../../core/models/EdgeInfo';
import { RelationCategory } from '../../../../core/models/types';

@Component({
  selector: 'app-dependency-graph',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  templateUrl: './dependency-graph.component.html',
  styleUrls: ['./dependency-graph.component.scss'],
})
export class DependencyGraphComponent implements OnDestroy {
  nodes = input.required<NodeInfo[]>();
  edges = input.required<EdgeInfo[]>();
  activeCategories = input.required<Set<RelationCategory>>();
  visibleNodeIds = input.required<Set<string>>();

  nodeSelected = output<NodeInfo | null>();
  categoryToggled = output<RelationCategory>();

  cyContainer = viewChild.required<ElementRef>('cyContainer');

  private cy: cytoscape.Core | null = null;
  private graphReady = signal(false);
  private lastDatasetKey = '';

  graphExport = output<string>();

  categories: { key: RelationCategory; label: string; color: string }[] = [
    { key: 'STRUCTURAL', label: 'Estrutural', color: '#2196F3' },
    { key: 'BEHAVIORAL', label: 'Comportamental', color: '#FF9800' },
    { key: 'LOGICAL', label: 'Lógica', color: '#4CAF50' },
  ];

  constructor() {
    afterNextRender(() => {
      this.initCytoscape();
      this.graphReady.set(true);
    });

    effect(() => {
      const nodes = this.nodes();
      const edges = this.edges();
      const ready = this.graphReady();
      const key = this.computeDatasetKey(nodes, edges);
      if (ready && this.cy && key !== this.lastDatasetKey) {
        this.lastDatasetKey = key;
        this.rebuildGraph(nodes, edges);
        this.applyVisibility(this.visibleNodeIds(), this.activeCategories());
      }
    });

    effect(() => {
      const visible = this.visibleNodeIds();
      const cats = this.activeCategories();
      const ready = this.graphReady();
      if (ready && this.cy) {
        this.applyVisibility(visible, cats);
      }
    });
  }

  private computeDatasetKey(nodes: NodeInfo[], edges: EdgeInfo[]): string {
    const firstN = nodes[0]?.id ?? '';
    const lastN = nodes[nodes.length - 1]?.id ?? '';
    const firstE = edges[0] ? `${edges[0].source}->${edges[0].target}` : '';
    return `${nodes.length}:${edges.length}:${firstN}:${lastN}:${firstE}`;
  }

  ngOnDestroy(): void {
    this.cy?.destroy();
  }

  exportPng(): void {
    if (!this.cy) return;
    const dataUrl = this.cy.png({ output: 'blob', bg: '#ffffff', scale: 2, full: true });
    const url = URL.createObjectURL(dataUrl as any);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'grafo-dependencias.png';
    a.click();
    URL.revokeObjectURL(url);
  }

  isCategoryActive(cat: RelationCategory): boolean {
    return this.activeCategories().has(cat);
  }

  private initCytoscape(): void {
    this.cy = cytoscape({
      container: this.cyContainer().nativeElement,
      style: this.buildStylesheet(),
      layout: { name: 'grid' },
      minZoom: 0.1,
      maxZoom: 5,
    });

    this.cy.on('tap', 'node', (evt) => {
      const nodeId = evt.target.id();
      const node = this.nodes().find((n) => n.id === nodeId) ?? null;
      this.nodeSelected.emit(node);
    });

    this.cy.on('tap', (evt) => {
      if (evt.target === this.cy) {
        this.nodeSelected.emit(null);
      }
    });

    const nodes = this.nodes();
    const edges = this.edges();
    this.lastDatasetKey = this.computeDatasetKey(nodes, edges);
    this.rebuildGraph(nodes, edges);
    this.applyVisibility(this.visibleNodeIds(), this.activeCategories());
  }

  private rebuildGraph(nodes: NodeInfo[], edges: EdgeInfo[]): void {
    if (!this.cy) return;
    this.cy.batch(() => {
      this.cy!.elements().remove();
      this.cy!.add(this.buildElements(nodes, edges));
    });
    this.cy
      .layout({
        name: 'cose',
        animate: false,
        idealEdgeLength: () => 120,
        nodeOverlap: 20,
        nodeRepulsion: () => 500000,
        gravity: 0.4,
        numIter: 500,
        fit: true,
        padding: 40,
      } as any)
      .run();
  }

  private buildElements(
    nodes: NodeInfo[],
    edges: EdgeInfo[],
  ): cytoscape.ElementDefinition[] {
    const nodeElements: cytoscape.ElementDefinition[] = nodes.map((n) => ({
      group: 'nodes',
      data: {
        id: n.id,
        label: n.simpleName,
        nodeType: n.type,
        cbo: n.metrics.cbo,
      },
    }));

    const nodeIds = new Set(nodes.map((n) => n.id));
    const edgeElements: cytoscape.ElementDefinition[] = edges
      .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map((e, i) => ({
        group: 'edges',
        data: {
          id: `e${i}`,
          source: e.source,
          target: e.target,
          relationType: e.type,
          category: e.category,
        },
      }));

    return [...nodeElements, ...edgeElements];
  }

  private applyVisibility(
    visibleNodeIds: Set<string>,
    activeCategories: Set<RelationCategory>,
  ): void {
    if (!this.cy) return;
    this.cy.batch(() => {
      this.cy!.nodes().forEach((node) => {
        node.style('display', visibleNodeIds.has(node.id()) ? 'element' : 'none');
      });
      this.cy!.edges().forEach((edge) => {
        const cat = edge.data('category') as RelationCategory;
        const src = edge.data('source') as string;
        const tgt = edge.data('target') as string;
        const show =
          activeCategories.has(cat) && visibleNodeIds.has(src) && visibleNodeIds.has(tgt);
        edge.style('display', show ? 'element' : 'none');
      });
    });
  }

  private buildStylesheet(): cytoscape.StylesheetStyle[] {
    return [
      {
        selector: 'node',
        style: {
          label: 'data(label)',
          'font-size': '9px',
          'text-valign': 'bottom',
          'text-halign': 'center',
          'text-margin-y': 4,
          width: 'mapData(cbo, 0, 30, 18, 60)',
          height: 'mapData(cbo, 0, 30, 18, 60)',
          'border-width': 1,
          'border-color': '#ccc',
        },
      },
      // Node colors by CBO threshold
      {
        selector: 'node[cbo <= 2]',
        style: { 'background-color': '#4CAF50' },
      },
      {
        selector: 'node[cbo > 2][cbo <= 5]',
        style: { 'background-color': '#FFC107' },
      },
      {
        selector: 'node[cbo > 5][cbo <= 10]',
        style: { 'background-color': '#FF9800' },
      },
      {
        selector: 'node[cbo > 10]',
        style: { 'background-color': '#f44336' },
      },
      // Node shapes by type
      {
        selector: 'node[nodeType = "INTERFACE"]',
        style: { shape: 'diamond' },
      },
      {
        selector: 'node[nodeType = "ENUM"]',
        style: { shape: 'triangle' },
      },
      {
        selector: 'node[nodeType = "RECORD"]',
        style: { shape: 'rectangle' },
      },
      // Selected node
      {
        selector: 'node:selected',
        style: { 'border-width': 3, 'border-color': '#1565C0' },
      },
      // Edge base
      {
        selector: 'edge',
        style: {
          width: 1,
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'arrow-scale': 0.7,
          opacity: 0.5,
        },
      },
      // Edge colors by category
      {
        selector: 'edge[category = "STRUCTURAL"]',
        style: { 'line-color': '#2196F3', 'target-arrow-color': '#2196F3' },
      },
      {
        selector: 'edge[category = "BEHAVIORAL"]',
        style: {
          'line-color': '#FF9800',
          'target-arrow-color': '#FF9800',
          'line-style': 'dashed',
        },
      },
      {
        selector: 'edge[category = "LOGICAL"]',
        style: {
          'line-color': '#4CAF50',
          'target-arrow-color': '#4CAF50',
          'line-style': 'dotted',
          width: 2,
        },
      },
    ];
  }
}
