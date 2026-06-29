import * as React from 'react';
import { useLayoutEffect, useRef } from 'react';
import { useIntl } from 'react-intl';

import { TUserListItem } from '../../../types/user';
import { IKickoff, ITemplateTask } from '../../../types/template';
import { TTaskVariable, TTaskFormPart, ETaskFormParts } from '../types';
import { TPatchTaskPayload } from '../../../redux/actions';
import { scrollToElement } from '../../../utils/helpers';
import { ShowMore } from '../../UI/ShowMore';
import { useTaskFormParts } from './useTaskFormParts';

import styles from '../TemplateEdit.css';

interface ITaskFormSectionsProps {
  accountId: number;
  currentTask: ITemplateTask;
  isSubscribed: boolean;
  isTeamInvitesModalOpen: boolean;
  kickoff: IKickoff;
  listVariables: TTaskVariable[];
  scrollTarget: TTaskFormPart;
  tasks: ITemplateTask[];
  templateId: number | undefined;
  users: TUserListItem[];
  wrapperRef: React.RefObject<HTMLDivElement>;
  handleTaskFieldChange(field: keyof ITemplateTask): (value: ITemplateTask[keyof ITemplateTask]) => void;
  patchTask(args: TPatchTaskPayload): void;
  setCurrentTask(changedFields: Partial<ITemplateTask>): void;
}

export function TaskFormSections({
  accountId,
  currentTask,
  handleTaskFieldChange,
  isSubscribed,
  isTeamInvitesModalOpen,
  kickoff,
  listVariables,
  patchTask,
  scrollTarget,
  setCurrentTask,
  tasks,
  templateId,
  users,
  wrapperRef,
}: ITaskFormSectionsProps) {
  const { formatMessage } = useIntl();
  const taskFormPartsRefs = {
    [ETaskFormParts.AssignPerformers]: useRef<HTMLDivElement>(null),
    [ETaskFormParts.DueIn]: useRef<HTMLDivElement>(null),
    [ETaskFormParts.Fields]: useRef<HTMLDivElement>(null),
    [ETaskFormParts.StartsAfter]: useRef<HTMLDivElement>(null),
    [ETaskFormParts.CheckIf]: useRef<HTMLDivElement>(null),
    [ETaskFormParts.ReturnTo]: useRef<HTMLDivElement>(null),
  };
  const taskFormParts = useTaskFormParts({
    accountId,
    currentTask,
    handleTaskFieldChange,
    isSubscribed,
    isTeamInvitesModalOpen,
    kickoff,
    listVariables,
    patchTask,
    isFieldsSectionShown: ETaskFormParts.Fields === scrollTarget,
    setCurrentTask,
    tasks,
    templateId,
    users,
  });

  useLayoutEffect(() => {
    const scrollTo = (scrollTarget && taskFormPartsRefs[scrollTarget]?.current) || wrapperRef.current;

    if (scrollTo) scrollToElement(scrollTo);
  }, []);

  return (
    <>
      {taskFormParts.map(({ title, component, formPartId, widget }) => (
        <ShowMore
          isDisabled={title === 'templates.return-to.title' && tasks.length < 2}
          label={formatMessage({ id: title })}
          containerClassName={styles['task-accordion-container']}
          isInitiallyVisible={formPartId === scrollTarget}
          key={title}
          innerRef={taskFormPartsRefs[formPartId]}
          widget={widget}
          isFromTaskForm
        >
          {component}
        </ShowMore>
      ))}
    </>
  );
}
