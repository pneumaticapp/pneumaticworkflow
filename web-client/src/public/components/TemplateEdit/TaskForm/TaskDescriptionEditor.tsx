import * as React from 'react';
import { useIntl } from 'react-intl';

import { TTaskVariable } from '../types';
import { getInitialEditorState } from '../../RichEditor/utils/сonverters';
import { RichEditor, RichEditorContainer } from '../../RichEditor';

import { variablesDecorator } from '../utils/variablesDecorator';
import { VariableList } from '../VariableList';
import { addVariableEntityToEditor } from '../utils/addVariableEntityToEditor';

import styles from '../TemplateEdit.css';

export interface ITaskDescriptionEditorProps {
  accountId: number;
  listVariables: TTaskVariable[];
  templateVariables: TTaskVariable[];
  value?: string;
  handleChange: React.ComponentProps<typeof RichEditor>['handleChange'];
  handleChangeChecklists: React.ComponentProps<typeof RichEditor>['handleChangeChecklists'];
}

export function TaskDescriptionEditor({
  accountId,
  listVariables,
  templateVariables,
  value,
  handleChange,
  handleChangeChecklists,
}: ITaskDescriptionEditorProps) {
  const editor = React.useRef<RichEditor>(null);
  const { formatMessage } = useIntl();

  const handleInsertVariable = (apiName?: string) => (e: React.MouseEvent) => {
    e.stopPropagation();

    if (!editor.current) {
      return;
    }

    const newVariable = listVariables?.find((variable) => variable.apiName === apiName);
    editor.current.onChange(
      addVariableEntityToEditor(editor.current.state.editorState, {
        title: newVariable?.title,
        subtitle: newVariable?.subtitle,
        apiName,
      }),
    );
  };

  return (
    <RichEditorContainer
      ref={editor}
      title={formatMessage({ id: 'tasks.task-description-field' })}
      placeholder={formatMessage({ id: 'template.task-description-placeholder' })}
      initialState={getInitialEditorState(value, templateVariables)}
      handleChange={handleChange}
      handleChangeChecklists={handleChangeChecklists}
      decorators={[variablesDecorator]}
      withChecklists
      accountId={accountId}
    >
      <VariableList
        variables={listVariables}
        onVariableClick={handleInsertVariable}
        className={styles['task-description__variables']}
        tooltipText="tasks.task-description-button-tooltip"
        focusEditor={() => editor.current?.focus()}
      />
    </RichEditorContainer>
  );
}
