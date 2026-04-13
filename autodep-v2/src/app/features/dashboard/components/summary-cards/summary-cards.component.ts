import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SummaryInfo } from '../../../../core/models/SummaryInfo';

@Component({
  selector: 'app-summary-cards',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './summary-cards.component.html',
  styleUrls: ['./summary-cards.component.scss'],
})
export class SummaryCardsComponent {
  summary = input.required<SummaryInfo>();
}
