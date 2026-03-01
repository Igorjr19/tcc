import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AnalysisResult } from '../../../../core/models/AnalysisResult';

@Component({
  selector: 'app-summary-cards',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './summary-cards.component.html',
  styleUrls: ['./summary-cards.component.scss'],
})
export class SummaryCardsComponent {
  data = input.required<AnalysisResult>();
}
