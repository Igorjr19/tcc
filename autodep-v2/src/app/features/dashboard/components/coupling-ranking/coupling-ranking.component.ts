import { Component, input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClassInfo } from '../../../../core/models/ClassInfo';
import { ProgressBarModule } from 'primeng/progressbar';

@Component({
  selector: 'app-coupling-ranking',
  standalone: true,
  imports: [CommonModule, ProgressBarModule],
  templateUrl: './coupling-ranking.component.html',
  styleUrls: ['./coupling-ranking.component.scss'],
})
export class CouplingRankingComponent {
  classes = input.required<ClassInfo[]>();

  topClasses = computed(() => {
    return [...this.classes()].sort((a, b) => b.totalCoupling - a.totalCoupling).slice(0, 10);
  });

  maxCoupling = computed(() => {
    const list = this.topClasses();
    return list.length > 0 ? list[0].totalCoupling : 0;
  });

  getPercentage(cbo: number): number {
    const max = this.maxCoupling();
    if (max === 0) return 0;
    return (cbo / max) * 100;
  }
}
