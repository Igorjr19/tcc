export type RelationType =
  | 'INHERITANCE'
  | 'INTERFACE_IMPLEMENTATION'
  | 'COMPOSITION'
  | 'AGGREGATION'
  | 'ASSOCIATION'
  | 'METHOD_CALL'
  | 'ATTRIBUTE_ACCESS'
  | 'TYPE_REFERENCE'
  | 'CO_CHANGE';

export type RelationCategory = 'STRUCTURAL' | 'BEHAVIORAL' | 'LOGICAL';

export type NodeType = 'CLASS' | 'INTERFACE' | 'ENUM' | 'RECORD';
