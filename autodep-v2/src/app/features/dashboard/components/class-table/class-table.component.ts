import { Component, input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClassInfo } from '../../../../core/models/ClassInfo';
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
  classes = input.required<ClassInfo[]>();

  getSeverity(cbo: number): 'success' | 'warn' | 'danger' | 'info' {
    if (cbo > 10) return 'danger';
    if (cbo > 5) return 'warn';
    if (cbo > 2) return 'info';
    return 'success';
  }

  getTypeLabel(cls: ClassInfo): string {
    if (cls.isInterface) return 'Interface';
    if (cls.isAbstract) return 'Abstrata';
    return 'Classe';
  }
}
