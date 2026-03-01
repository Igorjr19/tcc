import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { providePrimeNG } from 'primeng/config';
import Aura from '@primeuix/themes/aura';
import { provideEchartsCore } from 'ngx-echarts';

import { routes } from './app.routes';
import { ANALYSIS_SERVICE_TOKEN } from './core/services/AnalysisPort';
import { MockAnalysisService } from './core/services/MockAnalysisService';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideAnimationsAsync(),
    providePrimeNG({
      theme: { preset: Aura },
    }),
    provideEchartsCore({ echarts: () => import('echarts') }),
    { provide: ANALYSIS_SERVICE_TOKEN, useClass: MockAnalysisService },
  ],
};
