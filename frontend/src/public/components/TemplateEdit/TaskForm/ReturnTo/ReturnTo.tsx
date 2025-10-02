/* eslint-disable indent */
import React, { ReactNode, useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { DropdownList } from '../../../UI/DropdownList';
import { RichText } from '../../../RichText';
import { TrashIcon } from '../../../icons';
import { getFormattedDropdownOption } from '../Conditions/utils/getFormattedDropdownOption';
import { useCheckDevice } from '../../../../hooks/useCheckDevice';

import { TTaskVariable } from '../../types';
import { ITemplateTask } from '../../../../types/template';

import styles from './ReturnTo.css';
import stylesTaskForm from '../TaskForm.css';

interface IReturnToProps {
  variables: TTaskVariable[];
  tasks: ITemplateTask[];
  currentTaskRevertTask: string | null;
  setCurrentTask(changedFields: Partial<ITemplateTask>): void;
  taskAncestors: Set<string>;
}

interface IDropdownTask {
  label: string;
  apiName: string | null;
  richLabel: ReactNode;
}

export function ReturnTo({ variables, tasks, currentTaskRevertTask, setCurrentTask, taskAncestors }: IReturnToProps) {
  const [isReturnTo, setIsReturnTo] = useState(Boolean(currentTaskRevertTask));
  const { formatMessage } = useIntl();
  const { isMobile } = useCheckDevice();
  const STYLES = {
    option: styles['return-to__option'],
    container: classnames(
      styles['return-to__container'],
      stylesTaskForm['taskform__box'],
      isReturnTo ? stylesTaskForm['content-mt16'] : stylesTaskForm['content-mt12'],
    ),
    addReturn: classnames(styles['return-to__add-return'], stylesTaskForm['taskform__add-rule']),
    dropdownContainer: classnames(
      styles['return-to__dropdown-container'],
      stylesTaskForm['taskform__basket-visibility'],
    ),
    removeReturn: stylesTaskForm['taskform__remove-rule'],
  } as const;

  const TRANSLATIONS = {
    addReturn: 'templates.return-to.add-return',
    placeholder: isMobile ? 'templates.return-to.placeholder-mobile' : 'templates.return-to.placeholder',
    removeReturn: 'templates.return-to.remove-return',
  } as const;

  const dropdownTaskList = useMemo(
    () => [
      ...tasks
        .filter((task: ITemplateTask) => taskAncestors.has(task.apiName))
        .map(({ name, apiName }) => {
          return {
            label: name,
            apiName,
            richLabel: (
              <div className={STYLES.option}>
                <RichText text={name} variables={variables} />
              </div>
            ),
          };
        }),
    ],
    [tasks, variables, taskAncestors],
  );

  const selectedTask =
    currentTaskRevertTask && dropdownTaskList.find((task: IDropdownTask) => currentTaskRevertTask === task.apiName);

  const formatOptionLabel = (option: IDropdownTask, { context }: { context: string }) => {
    return context === 'menu'
      ? getFormattedDropdownOption({
          label: option.richLabel,
          isSelected: option.apiName === currentTaskRevertTask,
        })
      : option.richLabel;
  };

  const removeReturn = () => {
    setIsReturnTo(false);
    setCurrentTask({ revertTask: null });
  };

  const handleOptionChange = (option: IDropdownTask) => {
    if (selectedTask && option.apiName === selectedTask.apiName) return;
    setCurrentTask({ revertTask: option.apiName });
  };

  return (
    <div className={STYLES.container}>
      {!isReturnTo ? (
        <button type="button" onClick={() => setIsReturnTo(true)} className={STYLES.addReturn}>
          {formatMessage({ id: TRANSLATIONS.addReturn })}
        </button>
      ) : (
        <div className={STYLES.dropdownContainer}>
          <DropdownList<IDropdownTask>
            placeholder={formatMessage({ id: TRANSLATIONS.placeholder })}
            value={selectedTask}
            getOptionLabel={(option: any) => option.richLabel}
            onChange={handleOptionChange}
            options={dropdownTaskList}
            formatOptionLabel={formatOptionLabel}
          />

          <button
            type="button"
            aria-label={formatMessage({ id: TRANSLATIONS.removeReturn })}
            onClick={removeReturn}
            className={STYLES.removeReturn}
          >
            <TrashIcon />
          </button>
        </div>
      )}
    </div>
  );
}
