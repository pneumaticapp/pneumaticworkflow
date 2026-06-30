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
import { TMergedTaskOutputRow } from './mergeTaskOutputFlow';

import styles from '../OutputForm/OutputForm.css';
import kickoffStyles from '../KickoffRedux/KickoffRedux.css';

export interface IMergedOutputRowsProps {
  mergedRows: TMergedTaskOutputRow[];
  onDeleteField: (apiName: string) => void;
  onMoveRow: (index: number, direction: 'up' | 'down') => void;
  onEditField: (apiName: string) => (changedProps: Partial<IExtraField>) => void;
  onRemoveFieldset: (sharedFieldsetId: number) => void;
  datasetOptions: { value: string; label: string }[];
  accountId: number;
  formatMessage: (descriptor: { id: string }) => string;
  innerRef?: React.RefObject<HTMLInputElement>;
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
        const { name, fields, apiNameBinding } = mapFieldsetBindingClientToRuntime(row);
        const fieldsetTitle = name || formatMessage({ id: 'tasks.task-fieldsets' });
        return (
          <div
            key={`fieldset-${apiNameBinding}`}
            className={classNames(
              kickoffStyles['with-label'],
              kickoffStyles['kick-off-input'],
            )}
          >
            <div className={kickoffStyles['kick-off-input__field']}>
              <div
                className={classNames(kickoffStyles['kick-off-input__name-readonly'], styles['flow__fieldset-name'])}
                title={fieldsetTitle}
              >
                {formatMessage({ id: 'fieldsets.title' })}: {fieldsetTitle}
              </div>
              {isArrayWithItems(fields) &&
                <div className={styles['flow__fieldset-nested-fields']}>
                  <ExtraFieldsLabels extraFields={fields} />
                </div>
              }
            </div>
            <div className={kickoffStyles['kick-off-input__dropdown']}>
              {/* sharedFieldsetId is synced with FieldsetIconPicker — do not replace with apiNameBinding */}
              <FieldsetFlowRowDropdown
                headerTitle={fieldsetTitle}
                isFirstItem={isFirst}
                isLastItem={isLast}
                onMoveUp={() => onMoveRow(index, 'up')}
                onMoveDown={() => onMoveRow(index, 'down')}
                onRemove={() => onRemoveFieldset(row.sharedFieldsetId)}
              />
            </div>
          </div>
        );
      })}
    </>
  );
}
