import { ReactNode } from 'react';

import { ITemplateTaskClient } from '../../../../types/template';
import { TTaskVariable } from '../../types';

export interface IReturnToProps {
  variables: TTaskVariable[];
  tasks: ITemplateTaskClient[];
  taskAncestors: Set<string>;
}

export interface IDropdownTask {
  label: string;
  apiName: string | null;
  richLabel: ReactNode;
}
