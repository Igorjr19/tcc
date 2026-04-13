import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { providePrimeNG } from 'primeng/config';
import Aura from '@primeuix/themes/aura';

import { routes } from './app.routes';
import { ANALYSIS_SERVICE_TOKEN } from './core/services/AnalysisPort';
import { TauriAnalysisService } from './core/services/TauriAnalysisService';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideAnimationsAsync(),
    providePrimeNG({ theme: { preset: Aura } }),
    { provide: ANALYSIS_SERVICE_TOKEN, useClass: TauriAnalysisService },
  ],
};
