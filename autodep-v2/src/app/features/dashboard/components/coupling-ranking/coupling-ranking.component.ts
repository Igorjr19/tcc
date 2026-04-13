import { Component, input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NodeInfo } from '../../../../core/models/NodeInfo';

@Component({
  selector: 'app-coupling-ranking',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './coupling-ranking.component.html',
  styleUrls: ['./coupling-ranking.component.scss'],
})
export class CouplingRankingComponent {
  nodes = input.required<NodeInfo[]>();

  topNodes = computed(() =>
    [...this.nodes()].sort((a, b) => b.metrics.cbo - a.metrics.cbo).slice(0, 10),
  );
}
