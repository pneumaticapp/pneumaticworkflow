/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';

import {
  ContentBlock,
  ContentState,
  CompositeDecorator,
} from 'draft-js';
import { Badge } from '../../../utils/badge/Badge';
import { ECustomEditorEntities } from '../../RichEditor/utils/types';
import { isSystemVariable } from '../TaskForm/utils/getTaskVariables';

const findVariableEntities = (
  contentBlock: ContentBlock,
  callback: (start: number, end: number) => void,
  contentState: ContentState,
): void => {
  contentBlock.findEntityRanges((character) => {
    const entityKey = character.getEntity();

    return (
      entityKey !== null && contentState.getEntity(entityKey).getType() === ECustomEditorEntities.Variable
    );
  }, callback);
};

interface IVariableAdapterProps {
  entityKey: string;
  contentState: ContentState;
  children: React.ReactNode;
}

const VariableAdapter = (props: IVariableAdapterProps) => {
  const { formatMessage } = useIntl();
  const { subtitle, apiName } = props.contentState.getEntity(props.entityKey).getData();
  const isSystem = isSystemVariable(apiName);

  const localizedTitle = isSystem
    ? formatMessage({ id: `kickoff.system-varibale-${apiName}` })
    : props.children;

  const localizedSubtitle = isSystem
    ? formatMessage({ id: 'kickoff.system-varibale' })
    : subtitle;

  return <Badge subtitle={localizedSubtitle} title={localizedTitle} />;
};

export const variablesDecorator = new CompositeDecorator([
  {
    strategy: findVariableEntities,
    component: VariableAdapter,
  },
]);
