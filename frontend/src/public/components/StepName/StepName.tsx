/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { RichText } from '../RichText';
import type { IStepNameProps } from './types';

export function StepNameComponent({ initialStepName, templateId, variables, loadTemplateVariables }: IStepNameProps) {
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
