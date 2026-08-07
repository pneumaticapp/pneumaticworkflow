import * as React from 'react';
import classNames from 'classnames';

import { EInputNameBackgroundColor } from '../../../types/workflow';
import { EExtraFieldMode, IExtraField } from '../../../types/template';
import { mapFieldsetBindingClientToRuntime } from '../../../utils/mapFieldsetBindingClientToRuntime';
import { EFieldLabelPosition } from '../../../types/fieldset';
import { isArrayWithItems } from '../../../utils/helpers';
import { ExtraFieldIntl } from '../ExtraFields';
import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { FieldsetFlowRowDropdown } from './FieldsetFlowRowDropdown';
import { FieldsetEditorTitle } from './FieldsetEditorTitle';
import { TMergedTaskOutputRow } from './mergeTaskOutputFlow';

import styles from '../OutputForm/OutputForm.css';
import kickoffStyles from '../KickoffRedux/KickoffRedux.css';

export interface IMergedOutputRowsProps {
  mergedRows: TMergedTaskOutputRow[];
  onDeleteField: (apiName: string) => void;
  onMoveRow: (index: number, direction: 'up' | 'down') => void;
  onEditField: (apiName: string) => (changedProps: Partial<IExtraField>) => void;
  onRemoveFieldset: (apiNameBinding: string) => void;
  datasetOptions: { value: string; label: string }[];
  accountId: number;
  formatMessage: (descriptor: { id: string }) => string;
  innerRef?: React.RefObject<HTMLInputElement>;
  onEditFieldsetTitle: (apiNameBinding: string, title: string) => void;
}

export function MergedOutputRows({
  mergedRows,
  onDeleteField,
  onMoveRow,
  onEditField,
  onRemoveFieldset,
  datasetOptions,
  accountId,
  formatMessage,
  innerRef,
  onEditFieldsetTitle,
}: IMergedOutputRowsProps) {
  return (
    <>
      {mergedRows.map((row, index) => {
        const isFirst = index === 0;
        const isLast = index === mergedRows.length - 1;
        if (row.kind === 'field') {
          return (
            <ExtraFieldIntl
              key={row.field.apiName}
              id={index}
              field={{ ...row.field }}
              fieldsCount={mergedRows.length}
              labelBackgroundColor={EInputNameBackgroundColor.White}
              deleteField={() => onDeleteField(row.field.apiName)}
              moveFieldUp={isFirst ? undefined : () => onMoveRow(index, 'up')}
              moveFieldDown={isLast ? undefined : () => onMoveRow(index, 'down')}
              editField={onEditField(row.field.apiName)}
              isDisabled={false}
              innerRef={innerRef}
              accountId={accountId}
              mode={EExtraFieldMode.Kickoff}
              showDropdown
              datasetOptions={datasetOptions}
              labelPosition={EFieldLabelPosition.Top}
            />
          );
        }
        const { name, title, fields, apiNameBinding } = mapFieldsetBindingClientToRuntime(row);
        return (
          <div
            key={`fieldset-${apiNameBinding}`}
            className={classNames(
              kickoffStyles['with-label'],
              kickoffStyles['kick-off-input'],
              styles['flow__fieldset-row'],
            )}
          >
            <div className={kickoffStyles['kick-off-input__field']}>
              <div className={styles['flow__fieldset-header']}>
                {formatMessage({ id: 'fieldsets.header-label' })}
              </div>
              <div className={styles['flow__fieldset-name-row']}>
                <span className={styles['flow__fieldset-label']}>
                  {formatMessage({ id: 'fieldsets.name-label' })}:
                </span>{' '}
                {name}
              </div>
              <FieldsetEditorTitle
                apiNameBinding={apiNameBinding}
                title={title}
                onEditFieldsetTitle={onEditFieldsetTitle}
                formatMessage={formatMessage}
              />
              {isArrayWithItems(fields) &&
                <div className={styles['flow__fieldset-nested-fields']}>
                  <ExtraFieldsLabels extraFields={fields} />
                </div>
              }
            </div>
            <div className={kickoffStyles['kick-off-input__dropdown']}>
              <FieldsetFlowRowDropdown
                headerTitle={title}
                isFirstItem={isFirst}
                isLastItem={isLast}
                onMoveUp={() => onMoveRow(index, 'up')}
                onMoveDown={() => onMoveRow(index, 'down')}
                onRemove={() => onRemoveFieldset(row.apiNameBinding)}
              />
            </div>
          </div>
        );
      })}
    </>
  );
}
