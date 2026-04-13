import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';

import { AnalysisFacade } from '../../core/state/AnalysisFacade';
import { RelationCategory } from '../../core/models/types';
import { SummaryCardsComponent } from './components/summary-cards/summary-cards.component';
import { ClassTableComponent } from './components/class-table/class-table.component';
import { DependencyGraphComponent } from './components/dependency-graph/dependency-graph.component';
import { CouplingRankingComponent } from './components/coupling-ranking/coupling-ranking.component';
import { MetricsPanelComponent } from './components/metrics-panel/metrics-panel.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    ButtonModule,
    CardModule,
    SummaryCardsComponent,
    ClassTableComponent,
    DependencyGraphComponent,
    CouplingRankingComponent,
    MetricsPanelComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent {
  facade = inject(AnalysisFacade);

  onCategoryToggled(cat: RelationCategory): void {
    this.facade.toggleCategory(cat);
  }
}
