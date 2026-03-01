import { Component, inject } from '@angular/core';
import { AnalysisFacade } from '../../core/state/AnalysisFacade';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';

import { SummaryCardsComponent } from './components/summary-cards/summary-cards.component';
import { ClassTableComponent } from './components/class-table/class-table.component';
import { DependencyGraphComponent } from './components/dependency-graph/dependency-graph.component';
import { CouplingRankingComponent } from './components/coupling-ranking/coupling-ranking.component';

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
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent {
  public facade = inject(AnalysisFacade);
}
