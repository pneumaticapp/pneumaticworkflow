import React, { ComponentProps, useMemo, useRef } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { TTaskVariable } from '../types';
import { getInitialEditorState } from '../../RichEditor/utils/converters';
import { RichEditor, IRichEditorHandle } from '../../RichEditor';
import { LexicalRichEditor, ILexicalRichEditorHandle } from '../../RichEditor/lexical';
import { getMentionData } from '../../RichEditor/utils/getMentionData';
import { getUsers } from '../../../redux/selectors/user';
import { getNotDeletedUsers } from '../../../utils/users';

import { variablesDecorator } from '../utils/variablesDecorator';
import { VariableList } from '../VariableList';
import { addVariableEntityToEditor } from '../utils/addVariableEntityToEditor';

import styles from '../TemplateEdit.css';

const USE_LEXICAL_IN_TASK_DESCRIPTION = true;

export interface ITaskDescriptionEditorProps {
  accountId: number;
  listVariables: TTaskVariable[];
  templateVariables: TTaskVariable[];
  value?: string;
  handleChange: ComponentProps<typeof RichEditor>['handleChange'];
  handleChangeChecklists: ComponentProps<typeof RichEditor>['handleChangeChecklists'];
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

  const draftEditorRef = useRef<IRichEditorHandle>(null);
  const lexicalEditorRef = useRef<ILexicalRichEditorHandle>(null);
  const editorRef = USE_LEXICAL_IN_TASK_DESCRIPTION ? lexicalEditorRef : draftEditorRef;
  const { formatMessage } = useIntl();


  const handleInsertVariable = (apiName?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();

    if (!editorRef.current) {
      return;
    }

    if (USE_LEXICAL_IN_TASK_DESCRIPTION) {
      if (apiName == null) return;
      const newVariable = listVariables?.find((variable) => variable.apiName === apiName);
      (editorRef.current as ILexicalRichEditorHandle).insertVariable(
        apiName,
        newVariable?.title ?? '',
        newVariable?.subtitle ?? '',
      );
      return;
    }

    const newVariable = listVariables?.find((variable) => variable.apiName === apiName);
    (editorRef.current as IRichEditorHandle).onChange(
      addVariableEntityToEditor((editorRef.current as IRichEditorHandle).getEditorState(), {
        title: newVariable?.title,
        subtitle: newVariable?.subtitle,
        apiName,
      }),
    );
  };

  const titleMsg = formatMessage({ id: 'tasks.task-description-field' });
  const placeholderMsg = formatMessage({ id: 'template.task-description-placeholder' });

  if (USE_LEXICAL_IN_TASK_DESCRIPTION) {
    return (
      <LexicalRichEditor
        ref={lexicalEditorRef}
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
          focusEditor={() => lexicalEditorRef.current?.focus()}
        />
      </LexicalRichEditor>
    );
  }

  return (
    <RichEditor
      ref={draftEditorRef}
      title={titleMsg}
      placeholder={placeholderMsg}
      initialState={getInitialEditorState(value, templateVariables)}
      handleChange={handleChange}
      handleChangeChecklists={handleChangeChecklists}
      decorators={[variablesDecorator]}
      withChecklists
      accountId={accountId}
      isInTaskDescriptionEditor
      templateVariables={templateVariables}
    >
      <VariableList
        variables={listVariables}
        onVariableClick={handleInsertVariable}
        className={styles['task-description__variables']}
        tooltipText="tasks.task-description-button-tooltip"
        focusEditor={() => draftEditorRef.current?.focus()}
      />
    </RichEditor>
  );
}
