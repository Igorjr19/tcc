import { Injectable } from '@angular/core';
import { AnalysisPort } from './AnalysisPort';
import { AnalysisResult } from '../models/AnalysisResult';

@Injectable({
  providedIn: 'root',
})
export class MockAnalysisService implements AnalysisPort {
  async openFolderPicker(): Promise<string | null> {
    // Simulate folder picking delay
    await new Promise((resolve) => setTimeout(resolve, 500));
    return '/home/user/workspace/mock-project';
  }

  async analyzeProject(projectPath: string): Promise<AnalysisResult> {
    // Simulate analysis delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Return dummy data
    return {
      projectName: 'mock-project',
      projectPath: projectPath,
      projectGroupId: 'com.mock.app',
      totalClasses: 3,
      averageCoupling: 3.5,
      maxCoupling: 12,
      highlyCoupledClasses: 1,
      classes: [
        {
          className: 'com.mock.app.UserService',
          simpleName: 'UserService',
          packageName: 'com.mock.app',
          filePath: '/home/user/workspace/mock-project/src/main/java/com/mock/app/UserService.java',
          isInterface: false,
          isAbstract: false,
          methodCount: 5,
          fieldCount: 2,
          dependsOn: ['com.mock.app.UserRepository', 'com.mock.app.EmailService'],
          dependedByClasses: ['com.mock.app.UserController'],
          couplingOut: 2,
          couplingIn: 1,
          totalCoupling: 3,
          instability: 0.66,
        },
        {
          className: 'com.mock.app.UserRepository',
          simpleName: 'UserRepository',
          packageName: 'com.mock.app',
          filePath:
            '/home/user/workspace/mock-project/src/main/java/com/mock/app/UserRepository.java',
          isInterface: true,
          isAbstract: true,
          methodCount: 3,
          fieldCount: 0,
          dependsOn: [],
          dependedByClasses: ['com.mock.app.UserService'],
          couplingOut: 0,
          couplingIn: 1,
          totalCoupling: 1,
          instability: 0.0,
        },
        {
          className: 'com.mock.app.UserController',
          simpleName: 'UserController',
          packageName: 'com.mock.app',
          filePath:
            '/home/user/workspace/mock-project/src/main/java/com/mock/app/UserController.java',
          isInterface: false,
          isAbstract: false,
          methodCount: 2,
          fieldCount: 1,
          dependsOn: ['com.mock.app.UserService'],
          dependedByClasses: [],
          couplingOut: 1,
          couplingIn: 0,
          totalCoupling: 1,
          instability: 1.0,
        },
      ],
    };
  }

  async exportResults(data: string, format: string): Promise<string | null> {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return `/home/user/downloads/export.${format}`;
  }
}
