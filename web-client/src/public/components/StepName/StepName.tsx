/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { TLoadTemplateVariablesPayload } from '../../redux/actions';
import { RichText } from '../RichText';

import { TTaskVariable } from '../TemplateEdit/types';

export interface IStepNameProps {
  initialStepName: string;
  templateId: number;
  variables?: TTaskVariable[];
  loadTemplateVariables(payload: TLoadTemplateVariablesPayload): void;
}

export function StepNameComponent({
  initialStepName,
  templateId,
  variables,
  loadTemplateVariables,
}: IStepNameProps) {
  React.useEffect(() => {
    if (!variables) {
      loadTemplateVariables({ templateId });
    }
  }, []);

  if (!variables) {
    return <>{initialStepName}</>;
  }

  return <RichText text={initialStepName} variables={variables} isMarkdownMode={false} />;
}
