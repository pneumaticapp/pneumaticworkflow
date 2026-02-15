import React, { useMemo, useRef } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { TTaskVariable } from '../types';
import { RichEditor, type IRichEditorHandle } from '../../RichEditor';
import { getMentionData } from '../../RichEditor/utils/getMentionData';
import { getUsers } from '../../../redux/selectors/user';
import { getNotDeletedUsers } from '../../../utils/users';

import { VariableList } from '../VariableList';

import styles from '../TemplateEdit.css';

export interface ITaskDescriptionEditorProps {
  accountId: number;
  listVariables: TTaskVariable[];
  templateVariables: TTaskVariable[];
  value?: string;
  handleChange(value: string): Promise<string>;
  handleChangeChecklists?(checklists: import('../../../types/template').TOutputChecklist[]): void;
}

export function TaskDescriptionEditor({
  accountId,
  listVariables,
  templateVariables,
  value,
  handleChange,
  handleChangeChecklists,
}: ITaskDescriptionEditorProps) {
  const { formatMessage } = useIntl();
  const editorRef = useRef<IRichEditorHandle>(null);

  const users = useSelector(getUsers);
  const mentions = useMemo(
    () => getMentionData(getNotDeletedUsers(users)),
    [users],
  );

  const handleInsertVariable = (apiName?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();

    if (!editorRef.current || apiName == null) return;
    
    const newVariable = listVariables?.find((variable) => variable.apiName === apiName);

    if (!newVariable) return;

    editorRef.current.insertVariable(
      apiName,
      newVariable.title,
      newVariable.subtitle,
    );
  };

  return (
    <RichEditor
      ref={editorRef}
      title={formatMessage({ id: 'tasks.task-description-field' })}
      placeholder={formatMessage({ id: 'template.task-description-placeholder' })}
      defaultValue={value}
      handleChange={handleChange}
      handleChangeChecklists={handleChangeChecklists}
      withChecklists
      mentions={mentions}
      isInTaskDescriptionEditor
      templateVariables={templateVariables}
      accountId={accountId}
    >
      <VariableList
        variables={listVariables}
        onVariableClick={handleInsertVariable}
        className={styles['task-description__variables']}
        tooltipText="tasks.task-description-button-tooltip"
        focusEditor={() => editorRef.current?.focus()}
      />
    </RichEditor>
  );
}
