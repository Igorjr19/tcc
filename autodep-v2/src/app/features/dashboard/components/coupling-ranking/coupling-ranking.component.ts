import { Component, input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClassInfo } from '../../../../core/models/ClassInfo';

@Component({
  selector: 'app-coupling-ranking',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './coupling-ranking.component.html',
  styleUrls: ['./coupling-ranking.component.scss'],
})
export class CouplingRankingComponent {
  classes = input.required<ClassInfo[]>();

  topClasses = computed(() => {
    return [...this.classes()].sort((a, b) => b.totalCoupling - a.totalCoupling).slice(0, 10);
  });
}
