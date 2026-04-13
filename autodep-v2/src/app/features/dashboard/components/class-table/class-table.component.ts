import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NodeInfo } from '../../../../core/models/NodeInfo';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';

@Component({
  selector: 'app-class-table',
  standalone: true,
  imports: [CommonModule, TableModule, TagModule],
  templateUrl: './class-table.component.html',
  styleUrls: ['./class-table.component.scss'],
})
export class ClassTableComponent {
  nodes = input.required<NodeInfo[]>();

  getCboSeverity(cbo: number): 'success' | 'warn' | 'danger' | 'info' {
    if (cbo > 10) return 'danger';
    if (cbo > 5) return 'warn';
    if (cbo > 2) return 'info';
    return 'success';
  }

  getLcomSeverity(lcom: number): 'success' | 'warn' | 'danger' | 'info' {
    if (lcom > 0.8) return 'danger';
    if (lcom > 0.5) return 'warn';
    return 'success';
  }
}
