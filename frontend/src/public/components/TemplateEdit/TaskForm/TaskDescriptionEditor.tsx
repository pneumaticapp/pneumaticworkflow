import React, { ComponentProps, useRef } from 'react';
import { useIntl } from 'react-intl';

import { TTaskVariable } from '../types';
import { getInitialEditorState } from '../../RichEditor/utils/converters';
import { RichEditor, IRichEditorHandle } from '../../RichEditor';

import { variablesDecorator } from '../utils/variablesDecorator';
import { VariableList } from '../VariableList';
import { addVariableEntityToEditor } from '../utils/addVariableEntityToEditor';

import styles from '../TemplateEdit.css';

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
  const editor = useRef<IRichEditorHandle>(null);
  const { formatMessage } = useIntl();

  const handleInsertVariable = (apiName?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();

    if (!editor.current) {
      return;
    }

    const newVariable = listVariables?.find((variable) => variable.apiName === apiName);
    editor.current.onChange(
      addVariableEntityToEditor(editor.current.getEditorState(), {
        title: newVariable?.title,
        subtitle: newVariable?.subtitle,
        apiName,
      }),
    );
  };

  return (
    <RichEditor
      ref={editor}
      title={formatMessage({ id: 'tasks.task-description-field' })}
      placeholder={formatMessage({ id: 'template.task-description-placeholder' })}
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
        focusEditor={() => editor.current?.focus()}
      />
    </RichEditor>
  );
}
