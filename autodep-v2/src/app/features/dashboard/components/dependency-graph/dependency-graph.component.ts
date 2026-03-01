import { Component, input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgxEchartsModule, NGX_ECHARTS_CONFIG } from 'ngx-echarts';
import { ClassInfo } from '../../../../core/models/ClassInfo';
import * as echarts from 'echarts'; // Needs to provide echarts instance

@Component({
  selector: 'app-dependency-graph',
  standalone: true,
  imports: [CommonModule, NgxEchartsModule],
  providers: [
    {
      provide: NGX_ECHARTS_CONFIG,
      useValue: { echarts: () => import('echarts') },
    },
  ],
  templateUrl: './dependency-graph.component.html',
  styleUrls: ['./dependency-graph.component.scss'],
})
export class DependencyGraphComponent {
  classes = input.required<ClassInfo[]>();

  options = computed(() => {
    const classList = this.classes();
    const nodes = classList.map((c) => {
      let color = '#4CAF50';
      if (c.totalCoupling > 10) color = '#f44336';
      else if (c.totalCoupling > 5) color = '#FF9800';
      else if (c.totalCoupling > 2) color = '#FFC107';

      let symbol = 'circle';
      if (c.isInterface) symbol = 'diamond';
      else if (c.isAbstract) symbol = 'triangle';

      return {
        id: c.className,
        name: c.simpleName,
        symbol: symbol,
        symbolSize: Math.max(20, c.totalCoupling * 2 + 10),
        itemStyle: { color },
      };
    });

    const edges: any[] = [];
    const classMap = new Set(classList.map((c) => c.className));

    classList.forEach((c) => {
      c.dependsOn.forEach((dep) => {
        if (classMap.has(dep)) {
          edges.push({
            source: c.className,
            target: dep,
            lineStyle: { width: 1, curveness: 0.2, opacity: 0.6 },
          });
        }
      });
    });

    return {
      tooltip: {},
      animationDurationUpdate: 1500,
      animationEasingUpdate: 'quinticInOut' as any,
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          label: { show: true, position: 'right' },
          edgeSymbol: ['none', 'arrow'],
          edgeSymbolSize: [4, 10],
          force: {
            repulsion: 1000,
            edgeLength: [50, 200],
          },
          data: nodes,
          links: edges,
        },
      ],
    };
  });
}
