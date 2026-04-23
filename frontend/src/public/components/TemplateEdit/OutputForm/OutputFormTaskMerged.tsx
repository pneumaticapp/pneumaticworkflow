import * as React from 'react';
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import classNames from 'classnames';
import { IntlShape } from 'react-intl';

import { EInputNameBackgroundColor } from '../../../types/workflow';
import { EExtraFieldType, IExtraField, IFieldsetData, ITemplateTask } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { getEmptyField } from '../KickoffRedux/utils/getEmptyField';
import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../ExtraFields';
import { FieldsetIconPicker } from '../TaskOutputFlow/FieldsetIconPicker';
import { FieldsetFlowRowDropdown } from '../TaskOutputFlow/FieldsetFlowRowDropdown';
import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { updateFieldset } from '../../../api/fieldsets/updateFieldset';
import { NotificationManager } from '../../UI/Notifications/NotificationManager';
import { getErrorMessage } from '../../../utils/getErrorMessage';
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
  fieldsetsById: ReadonlyMap<number, IFieldsetData>;
  fieldsetsCatalogLoading: boolean;
  templateId: number | undefined;
  accountId: number;
  show?: boolean;
  patchTask: (args: TPatchTaskPayload) => void;
  intl: IntlShape;
}

function buildEffectiveFieldsetsMap(
  fieldsetsById: ReadonlyMap<number, IFieldsetData>,
  orderOverride: ReadonlyMap<number, number>,
): ReadonlyMap<number, IFieldsetData> {
  const next = new Map<number, IFieldsetData>();
  fieldsetsById.forEach((value, key) => {
    const o = orderOverride.get(key);
    next.set(key, o === undefined ? value : { ...value, order: o });
  });
  orderOverride.forEach((order, id) => {
    if (!next.has(id)) {
      next.set(id, {
        id,
        apiName: `fieldset-${id}`,
        name: '',
        description: '',
        fields: [],
        order,
      });
    }
  });
  return next;
}

export function OutputFormTaskMerged({
  task,
  fieldsetsById,
  fieldsetsCatalogLoading,
  templateId,
  accountId,
  show,
  patchTask,
  intl,
}: IOutputFormTaskMergedOwnProps) {
  const { formatMessage } = intl;
  const outputRef = useRef<HTMLInputElement>(null);
  const [fieldsetOrderOverride, setFieldsetOrderOverride] = useState<ReadonlyMap<number, number>>(() => new Map());

  useEffect(() => {
    if (show) {
      outputRef.current?.focus();
    }
  }, [show]);

  const effectiveFieldsetsById = useMemo(
    () => buildEffectiveFieldsetsMap(fieldsetsById, fieldsetOrderOverride),
    [fieldsetsById, fieldsetOrderOverride],
  );

  const mergedRows = useMemo(
    () => buildMergedTaskOutputRows(task.fields || [], task.fieldsets || [], effectiveFieldsetsById),
    [task.fields, task.fieldsets, effectiveFieldsetsById],
  );

  const persistMergedRows = useCallback(
    async (
      rows: TMergedTaskOutputRow[],
      explicitFieldsetIds?: number[],
      allFieldsSource?: IExtraField[],
    ) => {
      const allFields = allFieldsSource ?? task.fields ?? [];
      const fieldsetIdsList = explicitFieldsetIds ?? task.fieldsets ?? [];
      const { nextFields, fieldsetOrderPatches } = normalizeMergedTaskOutputOrders(rows, allFields);
      try {
        await Promise.all(fieldsetOrderPatches.map((p) => updateFieldset({ id: p.id, order: p.order })));
      } catch (error: unknown) {
        NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
        return;
      }
      setFieldsetOrderOverride((prev) => {
        const next = new Map(prev);
        fieldsetOrderPatches.forEach((p) => next.set(p.id, p.order));
        return next;
      });
      const orderOfFieldset = (id: number): number =>
        fieldsetOrderPatches.find((p) => p.id === id)?.order
        ?? effectiveFieldsetsById.get(id)?.order
        ?? 0;
      const nextFieldsetIds = [...fieldsetIdsList].sort((a, b) => orderOfFieldset(b) - orderOfFieldset(a));
      patchTask({
        taskUUID: task.uuid,
        changedFields: { fields: nextFields, fieldsets: nextFieldsetIds },
      });
    },
    [effectiveFieldsetsById, patchTask, task.fields, task.fieldsets, task.uuid],
  );

  const handleCreateField = useCallback(
    (type: EExtraFieldType) => {
      const newField = getEmptyField(type, formatMessage);
      const mergedTaskFields = [...(task.fields || []), newField];
      const rowsWithNew = buildMergedTaskOutputRows(
        mergedTaskFields,
        task.fieldsets || [],
        effectiveFieldsetsById,
      );
      persistMergedRows(rowsWithNew, undefined, mergedTaskFields).catch(() => undefined);
    },
    [effectiveFieldsetsById, formatMessage, persistMergedRows, task.fieldsets, task.fields],
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
      const rows = buildMergedTaskOutputRows(nextFields, task.fieldsets || [], effectiveFieldsetsById);
      persistMergedRows(rows, undefined, nextFields).catch(() => undefined);
    },
    [effectiveFieldsetsById, persistMergedRows, task.fieldsets, task.fields],
  );

  const handleMoveMergedIndex = useCallback(
    (index: number, direction: 'up' | 'down') => {
      const moved = moveMergedRow(mergedRows, index, direction);
      persistMergedRows(moved).catch(() => undefined);
    },
    [mergedRows, persistMergedRows],
  );

  const handleAddFieldset = useCallback(
    (fieldsetId: number) => {
      const current = task.fieldsets || [];
      if (current.includes(fieldsetId)) {
        return;
      }
      const nextIds = [...current, fieldsetId];
      const rows = buildMergedTaskOutputRows(task.fields || [], nextIds, effectiveFieldsetsById);
      persistMergedRows(rows, nextIds).catch(() => undefined);
    },
    [effectiveFieldsetsById, persistMergedRows, task.fieldsets, task.fields, task.uuid],
  );

  const handleRemoveFieldset = useCallback(
    (fieldsetId: number) => {
      const nextIds = (task.fieldsets || []).filter((id) => id !== fieldsetId);
      const rows = buildMergedTaskOutputRows(task.fields || [], nextIds, effectiveFieldsetsById);
      persistMergedRows(rows, nextIds).catch(() => undefined);
    },
    [effectiveFieldsetsById, persistMergedRows, task.fieldsets, task.fields, task.uuid],
  );

  useLayoutEffect(() => {
    setFieldsetOrderOverride(new Map());
  }, [task.uuid]);

  const isEmpty = !isArrayWithItems(task.fields) && !(task.fieldsets || []).length;

  return (
    <>
      <div className={classNames(styles['components'], stylesTaskForm['content-mt16'], styles['flow__components'])}>
        {ExtraFieldsMap.map((field) => (
          <ExtraFieldIcon {...field} key={field.id} onClick={() => handleCreateField(field.id)} />
        ))}
        <FieldsetIconPicker
          templateId={templateId}
          fieldsetsById={fieldsetsById}
          fieldsetsCatalogLoading={fieldsetsCatalogLoading}
          selectedFieldsetIds={task.fieldsets || []}
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
                />
              );
            }
            const fs = effectiveFieldsetsById.get(row.fieldsetId);
            const fieldsetTitle = fs?.name || formatMessage({ id: 'tasks.task-fieldsets' });
            return (
              <div
                key={`fieldset-${row.fieldsetId}`}
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
                    onRemove={() => handleRemoveFieldset(row.fieldsetId)}
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
