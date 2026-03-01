export interface ClassInfo {
  className: string;
  simpleName: string;
  packageName: string;
  filePath: string;
  isInterface: boolean;
  isAbstract: boolean;
  methodCount: number;
  fieldCount: number;
  dependsOn: string[];
  dependedByClasses: string[];
  couplingOut: number;
  couplingIn: number;
  totalCoupling: number;
  instability: number;
}
