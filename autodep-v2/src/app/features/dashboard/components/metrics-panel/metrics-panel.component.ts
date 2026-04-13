import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NodeInfo } from '../../../../core/models/NodeInfo';

@Component({
  selector: 'app-metrics-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './metrics-panel.component.html',
  styleUrls: ['./metrics-panel.component.scss'],
})
export class MetricsPanelComponent {
  node = input.required<NodeInfo>();
}
