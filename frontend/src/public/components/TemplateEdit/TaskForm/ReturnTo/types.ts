import { ReactNode } from 'react';

import { ITemplateTask } from '../../../../types/template';
import { TTaskVariable } from '../../types';

export interface IReturnToProps {
  variables: TTaskVariable[];
  tasks: ITemplateTask[];
  taskAncestors: Set<string>;
}

export interface IDropdownTask {
  label: string;
  apiName: string | null;
  richLabel: ReactNode;
}
