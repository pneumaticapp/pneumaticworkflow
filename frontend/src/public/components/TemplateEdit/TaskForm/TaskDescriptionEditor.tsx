import React, { useMemo, useRef } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { TTaskVariable } from '../types';
import { LexicalRichEditor, ILexicalRichEditorHandle } from '../../RichEditor/lexical';
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
  const users = useSelector(getUsers);
  const mentions = useMemo(
    () => getMentionData(getNotDeletedUsers(users)),
    [users],
  );

  const editorRef = useRef<ILexicalRichEditorHandle>(null);
  const { formatMessage } = useIntl();

  const handleInsertVariable = (apiName?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!editorRef.current || apiName == null) return;
    const newVariable = listVariables?.find((variable) => variable.apiName === apiName);
    editorRef.current.insertVariable(
      apiName,
      newVariable?.title ?? '',
      newVariable?.subtitle ?? '',
    );
  };

  const titleMsg = formatMessage({ id: 'tasks.task-description-field' });
  const placeholderMsg = formatMessage({ id: 'template.task-description-placeholder' });

  return (
    <LexicalRichEditor
      ref={editorRef}
      title={titleMsg}
      placeholder={placeholderMsg}
      defaultValue={value}
      handleChange={handleChange}
      handleChangeChecklists={handleChangeChecklists}
      withChecklists
      withToolbar
      withMentions
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
    </LexicalRichEditor>
  );
}
