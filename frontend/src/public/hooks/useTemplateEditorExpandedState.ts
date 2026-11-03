import { useCallback, useEffect, useState } from 'react';

import { TTemplateEditorExpandedState } from '../components/TemplateEdit/types';

export interface ITemplateEditorExpandedState {
  openedTasks: TTemplateEditorExpandedState;
  openedDelays: TTemplateEditorExpandedState;
  toggleTask(taskUuid: string): void;
  toggleDelay(taskUuid: string): void;
}

export function useTemplateEditorExpandedState(
  firstTaskUuid: string | undefined,
  shouldOpenFirstTask: boolean,
): ITemplateEditorExpandedState {
  const [openedTasks, setOpenedTasks] = useState<TTemplateEditorExpandedState>({});
  const [openedDelays, setOpenedDelays] = useState<TTemplateEditorExpandedState>({});

  useEffect(() => {
    if (!shouldOpenFirstTask || !firstTaskUuid) return;

    setOpenedTasks((current) => ({ ...current, [firstTaskUuid]: true }));
  }, [firstTaskUuid, shouldOpenFirstTask]);

  const toggleTask = useCallback((taskUuid: string): void => {
    setOpenedTasks((current) => ({ ...current, [taskUuid]: !current[taskUuid] }));
  }, []);

  const toggleDelay = useCallback((taskUuid: string): void => {
    setOpenedDelays((current) => ({ ...current, [taskUuid]: !current[taskUuid] }));
  }, []);

  return { openedTasks, openedDelays, toggleTask, toggleDelay };
}
