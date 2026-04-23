import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { ITemplateTask } from '../../../types/template';
import styles from '../ExtraFields/utils/ExtraFieldsLabels/ExtraFieldsLabels.css';
import { getTriplePlural } from '../../../utils/helpers';
import { useTemplateEditFieldsets } from '../TemplateEditFieldsetsContext';

interface ITaskRenderExtraFieldsInfoProps {
  task: ITemplateTask;
  onClick: () => void;
}

function countFieldsetOutputFields(
  fieldsetIds: number[] | undefined,
  fieldsetsById: ReadonlyMap<number, { fields: unknown[] }>,
): number {
  if (!fieldsetIds?.length) {
    return 0;
  }

  return fieldsetIds.reduce((acc, id) => acc + (fieldsetsById.get(id)?.fields.length ?? 0), 0);
}

export const TaskRenderExtraFieldsInfo = ({ task: { fields, fieldsets }, onClick }: ITaskRenderExtraFieldsInfoProps) => {
  const { formatMessage } = useIntl();
  const { fieldsetsById } = useTemplateEditFieldsets();

  const totalCount = useMemo(() => {
    return fields.length + countFieldsetOutputFields(fieldsets, fieldsetsById);
  }, [fieldsets, fieldsetsById, fields.length]);

  const extraFieldsText = getTriplePlural({
    counter: totalCount,
    forms: ['tasks.task-extra-field-single', 'tasks.task-extra-field-plural-1', 'tasks.task-extra-field-plural-2'],
    formatMessage,
  });

  return (
    totalCount > 0 && (
      <button className={styles['extra-field-label']} onClick={onClick} type="button">
        {extraFieldsText}
      </button>
    )
  );
};
