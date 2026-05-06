import * as React from 'react';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import classNames from 'classnames';
import { IntlShape } from 'react-intl';

import { EExtraFieldType, IExtraField, IFieldsetData, ITemplateTask } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { useDatasetOptions } from '../ExtraFields/utils/useDatasetOptions';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { getEmptyField } from '../KickoffRedux/utils/getEmptyField';
import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { FieldsetIconPicker } from '../TaskOutputFlow/FieldsetIconPicker';
import { MergedOutputRows } from '../TaskOutputFlow/MergedOutputRows';
import { TPatchTaskPayload } from '../../../redux/actions';

import {
  buildMergedTaskOutputRows,
  buildRowsWithAddedFieldset,
  buildRowsWithRemovedFieldset,
  moveMergedRow,
  normalizeMergedTaskOutputOrders,
  TMergedTaskOutputRow,
} from '../TaskOutputFlow/mergeTaskOutputFlow';

import styles from './OutputForm.css';
import stylesTaskForm from '../TaskForm/TaskForm.css';

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
  const datasetOptions = useDatasetOptions(task.fields || []);

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
      const newField = getEmptyField(type, formatMessage, -1);
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
      const rows = buildRowsWithAddedFieldset(task.fields || [], task.fieldsets || [], fieldsetApiName);
      if (rows) saveOutputOrders(rows).catch(() => undefined);
    },
    [saveOutputOrders, task.fieldsets, task.fields],
  );

  const handleRemoveFieldset = useCallback(
    (fieldsetApiName: string) => {
      const rows = buildRowsWithRemovedFieldset(task.fields || [], task.fieldsets || [], fieldsetApiName);
      saveOutputOrders(rows).catch(() => undefined);
    },
    [saveOutputOrders, task.fieldsets, task.fields],
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
          <MergedOutputRows
            mergedRows={mergedRows}
            fieldsetsByApiName={fieldsetsByApiName}
            onDeleteField={handleDeleteField}
            onMoveRow={handleMoveMergedIndex}
            onEditField={handleEditField}
            onRemoveFieldset={handleRemoveFieldset}
            datasetOptions={datasetOptions}
            accountId={accountId}
            formatMessage={formatMessage}
            innerRef={outputRef}
          />
        </div>
      )}
    </>
  );
}
