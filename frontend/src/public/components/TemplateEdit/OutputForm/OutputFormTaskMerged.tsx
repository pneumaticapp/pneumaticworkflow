import * as React from 'react';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import classNames from 'classnames';
import { IntlShape } from 'react-intl';

import { EInputNameBackgroundColor } from '../../../types/workflow';
import { EExtraFieldMode, EExtraFieldType, IExtraField, IFieldsetData, ITaskFieldset, ITemplateTask } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { getEmptyField } from '../KickoffRedux/utils/getEmptyField';
import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../ExtraFields';
import { FieldsetIconPicker } from '../TaskOutputFlow/FieldsetIconPicker';
import { FieldsetFlowRowDropdown } from '../TaskOutputFlow/FieldsetFlowRowDropdown';
import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { TPatchTaskPayload } from '../../../redux/actions';

import {
  buildMergedTaskOutputRows,
  moveMergedRow,
  normalizeMergedTaskOutputOrders,
  TMergedTaskOutputRow,
} from '../TaskOutputFlow/mergeTaskOutputFlow';

import styles from './OutputForm.css';
import stylesTaskForm from '../TaskForm/TaskForm.css';
import kickoffStyles from '../KickoffRedux/KickoffRedux.css';

export interface IOutputFormTaskMergedOwnProps {
  task: ITemplateTask;
  fieldsetsByApiName: ReadonlyMap<string, IFieldsetData>;
  fieldsetsCatalogLoading: boolean;
  templateId: number | undefined;
  accountId: number;
  show?: boolean;
  patchTask: (args: TPatchTaskPayload) => void;
  intl: IntlShape;
}


export function OutputFormTaskMerged({
  task,
  fieldsetsByApiName,
  fieldsetsCatalogLoading,
  templateId,
  accountId,
  show,
  patchTask,
  intl,
}: IOutputFormTaskMergedOwnProps) {
  const { formatMessage } = intl;
  const outputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (show) {
      outputRef.current?.focus();
    }
  }, [show]);

  const mergedRows = useMemo(
    () => buildMergedTaskOutputRows(task.fields || [], task.fieldsets || []),
    [task.fields, task.fieldsets],
  );

  const saveOutputOrders = useCallback(
    async (
      rows: TMergedTaskOutputRow[],
      allFieldsSource?: IExtraField[],
    ) => {
      const allFields = allFieldsSource ?? task.fields ?? [];
      const { nextFields, fieldsetOrderPatches } = normalizeMergedTaskOutputOrders(rows, allFields);
      patchTask({
        taskUUID: task.uuid,
        changedFields: { fields: nextFields, fieldsets: fieldsetOrderPatches },
      });
    },
    [patchTask, task.fields, task.fieldsets, task.uuid],
  );

  const handleCreateField = useCallback(
    (type: EExtraFieldType) => {
      const newField = getEmptyField(type, formatMessage);
      const mergedTaskFields = [...(task.fields || []), newField];
      const rowsWithNew = buildMergedTaskOutputRows(
        mergedTaskFields,
        task.fieldsets || [],
      );
      saveOutputOrders(rowsWithNew, mergedTaskFields).catch(() => undefined);
    },
    [formatMessage, saveOutputOrders, task.fieldsets, task.fields],
  );

  const handleEditField = useCallback(
    (apiName: string) => (changedProps: Partial<IExtraField>) => {
      const newFields = getEditedFields(task.fields || [], apiName, changedProps);
      patchTask({ taskUUID: task.uuid, changedFields: { fields: newFields } });
    },
    [patchTask, task.fields, task.uuid],
  );

  const handleDeleteField = useCallback(
    (apiName: string) => {
      const nextFields = (task.fields || []).filter((f) => f.apiName !== apiName);
      const rows = buildMergedTaskOutputRows(nextFields, task.fieldsets || []);
      saveOutputOrders(rows, nextFields).catch(() => undefined);
    },
    [saveOutputOrders, task.fieldsets, task.fields],
  );

  const handleMoveMergedIndex = useCallback(
    (index: number, direction: 'up' | 'down') => {
      const moved = moveMergedRow(mergedRows, index, direction);
      saveOutputOrders(moved).catch(() => undefined);
    },
    [mergedRows, saveOutputOrders],
  );

  const handleAddFieldset = useCallback(
    (fieldsetApiName: string) => {
      const current = task.fieldsets || [];
      if (current.some((fieldSet) => fieldSet.apiName === fieldsetApiName)) {
        return;
      }
      const newFieldset: ITaskFieldset = { apiName: fieldsetApiName, order: current.length };
      const nextFieldsets = [...current, newFieldset];
      const rows = buildMergedTaskOutputRows(task.fields || [], nextFieldsets);
      saveOutputOrders(rows).catch(() => undefined);
    },
    [saveOutputOrders, task.fieldsets, task.fields, task.uuid],
  );

  const handleRemoveFieldset = useCallback(
    (fieldsetApiName: string) => {
      const nextFieldsets = (task.fieldsets || []).filter((fieldSet) => fieldSet.apiName !== fieldsetApiName);
      const rows = buildMergedTaskOutputRows(task.fields || [], nextFieldsets);
      saveOutputOrders(rows).catch(() => undefined);
    },
    [saveOutputOrders, task.fieldsets, task.fields, task.uuid],
  );


  const isEmpty = !isArrayWithItems(task.fields) && !(task.fieldsets || []).length;

  return (
    <>
      <div className={classNames(styles['components'], stylesTaskForm['content-mt16'], styles['flow__components'])}>
        {ExtraFieldsMap.map((field) => (
          <ExtraFieldIcon {...field} key={field.id} onClick={() => handleCreateField(field.id)} />
        ))}
        <FieldsetIconPicker
          templateId={templateId}
          fieldsetsByApiName={fieldsetsByApiName}
          fieldsetsCatalogLoading={fieldsetsCatalogLoading}
          selectedFieldsetApiNames={(task.fieldsets || []).map((fieldset) => fieldset.apiName)}
          onSelectFieldset={handleAddFieldset}
          onRemoveFieldset={handleRemoveFieldset}
        />
      </div>

      {!isEmpty && (
        <div className={styles['fields']}>
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
                  deleteField={() => handleDeleteField(row.field.apiName)}
                  moveFieldUp={isFirst ? undefined : () => handleMoveMergedIndex(index, 'up')}
                  moveFieldDown={isLast ? undefined : () => handleMoveMergedIndex(index, 'down')}
                  editField={handleEditField(row.field.apiName)}
                  isDisabled={false}
                  innerRef={outputRef}
                  accountId={accountId}
                  mode={EExtraFieldMode.Kickoff}
                />
              );
            }
            const fs = fieldsetsByApiName.get(row.apiName);
            const fieldsetTitle = fs?.name || formatMessage({ id: 'tasks.task-fieldsets' });
            return (
              <div
                key={`fieldset-${row.apiName}`}
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
                  {fs && isArrayWithItems(fs.fields) &&
                    <div className={styles['flow__fieldset-nested-fields']}>
                      <ExtraFieldsLabels extraFields={fs.fields} />
                    </div>
                  }
                </div>
                <div className={kickoffStyles['kick-off-input__dropdown']}>
                  <FieldsetFlowRowDropdown
                    headerTitle={fieldsetTitle}
                    isFirstItem={isFirst}
                    isLastItem={isLast}
                    onMoveUp={() => handleMoveMergedIndex(index, 'up')}
                    onMoveDown={() => handleMoveMergedIndex(index, 'down')}
                    onRemove={() => handleRemoveFieldset(row.apiName)}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
