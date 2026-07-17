import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { ITemplateTaskClient, IFieldsetBindingClient } from '../../../types/template';
import styles from '../ExtraFields/utils/ExtraFieldsLabels/ExtraFieldsLabels.css';
import { getTriplePlural } from '../../../utils/helpers';

interface ITaskRenderExtraFieldsInfoProps {
  task: ITemplateTaskClient;
  onClick: () => void;
}

function countFieldsetOutputFields(
  fieldsets: IFieldsetBindingClient[] | undefined,
): number {
  if (!fieldsets?.length) {
    return 0;
  }

  return fieldsets.reduce((acc, taskFieldset) => acc + taskFieldset.fields.length, 0);
}

export const TaskRenderExtraFieldsInfo = ({ task: { fields, fieldsets }, onClick }: ITaskRenderExtraFieldsInfoProps) => {
  const { formatMessage } = useIntl();

  const totalCount = useMemo(() => {
    return fields.length + countFieldsetOutputFields(fieldsets);
  }, [fieldsets, fields.length]);

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
