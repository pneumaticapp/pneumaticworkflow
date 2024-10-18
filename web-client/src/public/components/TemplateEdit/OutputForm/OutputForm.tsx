/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { injectIntl, IntlShape } from 'react-intl';

import {
  EMoveDirections,
  EInputNameBackgroundColor,
} from '../../../types/workflow';
import {
  EExtraFieldType,
  IExtraField,
} from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../utils/workflows';

import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../ExtraFields';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { getEmptyField } from '../KickoffRedux/utils/getEmptyField';

import styles from './OutputForm.css';

export interface IOutputFormOwnProps {
  fields: IExtraField[];
  intl: IntlShape;
  show?: boolean;
  isDisabled: boolean;
  accountId: number;
  onOutputChange(value: IExtraField[]): void;
}

export function OutputForm({ fields, onOutputChange, intl, isDisabled, show, accountId }: IOutputFormOwnProps) {
  const outputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (show) {
      outputRef.current?.focus();
    }
  }, [outputRef]);

  const sortedFields = [...fields].sort((a, b) => b.order - a.order);

  const isFormEmpty = !isArrayWithItems(fields);

  const handleCreateField = (type: EExtraFieldType) => {
    const newFields = [...sortedFields, getEmptyField(type, intl.formatMessage)];

    onOutputChange(getNormalizeFieldsOrders(newFields));
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const newFields = getEditedFields(sortedFields, apiName, changedProps);
    onOutputChange(newFields);
  };

  const handleDeleteField = (idx: number) => {
    if (!onOutputChange) {
      return;
    }

    const newOutputFields = sortedFields.filter((_, index) => index !== idx);

    onOutputChange(getNormalizeFieldsOrders(newOutputFields));
  };

  const handleMoveField = (idx: number, direction: EMoveDirections) => {
    if (!onOutputChange) {
      return;
    }

    const to = direction === EMoveDirections.Up ? idx - 1 : idx + 1;

    const newOutputFields = moveWorkflowField(idx, to, sortedFields);

    onOutputChange(newOutputFields);
  };

  const renderOutputIcons = () => (
    <div className={styles['components']}>
      {ExtraFieldsMap.map(field => (
        <ExtraFieldIcon {...field} key={field.id} onClick={() => handleCreateField(field.id)} />
      ))}
    </div>
  );

  return (
    <>
      {!isDisabled && renderOutputIcons()}

      {!isFormEmpty && (
        <div className={styles['fields']}>
          {sortedFields.map((field, index) => (
            <ExtraFieldIntl
              key={index}
              id={index}
              field={{ ...field }}
              fieldsCount={sortedFields.length}
              labelBackgroundColor={EInputNameBackgroundColor.White}
              deleteField={() => handleDeleteField(index)}
              moveFieldUp={() => handleMoveField(index, EMoveDirections.Up)}
              moveFieldDown={() => handleMoveField(index, EMoveDirections.Down)}
              editField={handleEditField(field.apiName)}
              isDisabled={isDisabled}
              innerRef={outputRef}
              accountId={accountId}
            />),
          )}
        </div>
      )}

    </>
  );
}

export const OutputFormIntl = injectIntl(OutputForm);
