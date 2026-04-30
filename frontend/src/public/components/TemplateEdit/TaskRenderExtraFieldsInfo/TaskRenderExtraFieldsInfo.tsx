import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { ITemplateTask, ITaskFieldset } from '../../../types/template';
import styles from '../ExtraFields/utils/ExtraFieldsLabels/ExtraFieldsLabels.css';
import { getTriplePlural } from '../../../utils/helpers';
import { useTemplateEditFieldsets } from '../TemplateEditFieldsetsContext';

interface ITaskRenderExtraFieldsInfoProps {
  task: ITemplateTask;
  onClick: () => void;
}

function countFieldsetOutputFields(
  fieldsets: ITaskFieldset[] | undefined,
  fieldsetsByApiName: ReadonlyMap<string, { fields: unknown[] }>,
): number {
  if (!fieldsets?.length) {
    return 0;
  }

  return fieldsets.reduce((acc, taskFieldset) => acc + (fieldsetsByApiName.get(taskFieldset.apiName)?.fields.length ?? 0), 0);
}

export const TaskRenderExtraFieldsInfo = ({ task: { fields, fieldsets }, onClick }: ITaskRenderExtraFieldsInfoProps) => {
  const { formatMessage } = useIntl();
  const { fieldsetsByApiName } = useTemplateEditFieldsets();

  const totalCount = useMemo(() => {
    return fields.length + countFieldsetOutputFields(fieldsets, fieldsetsByApiName);
  }, [fieldsets, fieldsetsByApiName, fields.length]);

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
