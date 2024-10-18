/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import {
  ContentBlock,
  ContentState,
  CompositeDecorator,
} from 'draft-js';
import { Badge } from '../../../utils/badge/Badge';
import { ECustomEditorEntities } from '../../RichEditor/utils/types';

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
  const subtitle = props.contentState.getEntity(props.entityKey).getData().subtitle;

  return <Badge subtitle={subtitle} title={props.children} />;
};

export const variablesDecorator = new CompositeDecorator([
  {
    strategy: findVariableEntities,
    component: VariableAdapter,
  },
]);
