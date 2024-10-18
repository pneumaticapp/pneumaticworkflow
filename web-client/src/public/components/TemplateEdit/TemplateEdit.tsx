import React, { useState, useEffect } from 'react';
import classnames from 'classnames';
import TextareaAutosize from 'react-textarea-autosize';
import { useIntl } from 'react-intl';
import { RouteComponentProps } from 'react-router-dom';
import { debounce } from 'throttle-debounce';
import StickyBox from 'react-sticky-box';

import { IInfoWarningProps, InfoWarningsModal } from './InfoWarningsModal';
import { getClonedTask } from './utils/getClonedTask';
import { getEmptyConditions } from './TaskForm/Conditions/utils/getEmptyConditions';
import { AutoSaveStatusContainer } from './AutoSaveStatus';
import { TemplateEntity } from './TemplateEntity';
import { AddEntityButton, EEntityTitle } from './AddEntityButton';
import { EMPTY_DURATION, DEFAULT_TEMPLATE_NAME } from './constants';
import { getVariables } from './TaskForm/utils/getTaskVariables';
import { TemplateIntegrations } from './Integrations';
import { TemplateControllsContainer } from './TemplateControlls';

import { NAVBAR_HEIGHT } from '../../constants/defaultValues';
import { TemplateLastUpdateInfo } from './TemplateLastUpdateInfo';
import { ERoutes } from '../../constants/routes';
import { TUserListItem } from '../../types/user';
import { getEmptyKickoff, getNormalizedTemplateOwners, getTemplateIdFromUrl } from '../../utils/template';
import { checkSomeRouteIsActive, isCreateTemplate } from '../../utils/history';
import { KickoffReduxContainer } from './KickoffRedux';
import { moveTask } from '../../utils/workflows';
import { NotificationManager } from '../UI/Notifications';
import { isArrayWithItems } from '../../utils/helpers';
import { createTaskApiName, createUUID } from '../../utils/createId';
import { EMoveDirections } from '../../types/workflow';
import { ITemplate, ITemplateTask } from '../../types/template';
import { EditableText } from '../UI/EditableText';
import { TLoadTemplateVariablesSuccessPayload } from '../../redux/actions';
import { ETemplateStatus, IAuthUser } from '../../types/redux';
import { createEmptyDueDate } from '../../utils/dueDate/createEmptyDueDate';

import styles from './TemplateEdit.css';
import { usePrevious } from '../../hooks/usePrevious';
import { ConditionsBanner } from './ConditionsBanner';

export function TemplateEdit({
  match,
  location,
  authUser,
  template,
  aiTemplate,
  templateStatus,
  users,
  isSubscribed,
  loadTemplate,
  loadTemplateFromSystem,
  resetTemplateStore,
  saveTemplate,
  setTemplate,
  setTemplateStatus,
  loadTemplateVariablesSuccess,
}: TTemplateEditProps) {
  const { formatMessage } = useIntl();
  const {
    name: templateName,
    description: templateDescription,
    updatedBy,
    dateUpdated,
    tasks,
    templateOwners,
  } = template;

  const prevUsers = usePrevious(users);
  const prevLocation = usePrevious(location);
  const prevTemplate = usePrevious(template);

  const [openedTasks, setOpenedTasks] = useState<any>({});
  const [openedDelays, setOpenedDelays] = useState<any>({});
  const [isInfoWarningsModaOpen, setIsInfoWarningsModaOpen] = useState(false);
  const [infoWarnings, setInfoWarnings] = useState<any>([]);

  useEffect(() => {
    initPage();

    return () => {
      resetTemplateStore();
    };
  }, []);

  useEffect(() => {
    if (checkSomeRouteIsActive(ERoutes.TemplatesCreate) || checkSomeRouteIsActive(ERoutes.TemplatesCreateAI)) {
      openTask(template.tasks[0]?.uuid);
    }
  }, [template.tasks, prevLocation?.pathname]);

  useEffect(() => {
    const variables = getVariables(template);
    const prevVariables = prevTemplate ? getVariables(prevTemplate) : [];
    if (variables.length !== prevVariables.length) {
      if (template.id) {
        loadTemplateVariablesSuccess({ templateId: template.id, variables });
      }
    }

    const [pathName, prevPathName] = [location.pathname, prevLocation?.pathname];
    const isPreviousPathIsCreate = prevPathName === ERoutes.TemplatesCreate;
    const isCurrentPathIsEdit = checkSomeRouteIsActive(ERoutes.TemplatesEdit);
    const isCreateScenario = isPreviousPathIsCreate && isCurrentPathIsEdit;
    const isLocationChanged = pathName !== prevPathName;

    if (!isCreateScenario && isLocationChanged) {
      initPage();
      return;
    }

    if (users.length !== prevUsers?.length) {
      const newTemplateOwners = getNormalizedTemplateOwners(templateOwners, isSubscribed, users);
      setTemplate({ ...template, templateOwners: newTemplateOwners });
    }
  }, [prevTemplate, prevLocation, prevUsers]);

  const initPage = () => {
    const { id } = match.params as ITemplateEditParams;
    const workflowTemplateId = getTemplateIdFromUrl(location.search);
    const isCreateWorflowPage = isCreateTemplate();
    const isEditWorkflow = Boolean(id);
    const initMap = [
      {
        check: isCreateWorflowPage && workflowTemplateId,
        init: () => loadTemplateFromSystem(workflowTemplateId!),
      },
      {
        check: checkSomeRouteIsActive(ERoutes.TemplatesCreateAI),
        init: () => {
          const templateLocal = aiTemplate || getEmptyTemplate();
          setTemplate(templateLocal);
          saveTemplate();
        },
        name: '2',
      },
      {
        check: isCreateWorflowPage && !workflowTemplateId,
        init: () => setTemplate(getEmptyTemplate()),
      },
      {
        check: isEditWorkflow,
        init: () => loadTemplate(Number(id)),
      },
    ];
    const currentPageInit = initMap.find(({ check }) => check);

    if (currentPageInit) {
      currentPageInit.init();
    }
  };

  const openTask = (taskUUID?: string) => {
    if (!taskUUID) return;
    setOpenedTasks({ ...openedTasks, [taskUUID]: true });
  };

  const sortedTasks = () => [...tasks].sort((a, b) => a.number - b.number);

  const getNewTask = (templateTask?: Partial<ITemplateTask>): ITemplateTask => {
    return {
      apiName: createTaskApiName(),
      delay: null,
      description: '',
      name: 'New Step',
      number: 1,
      fields: [],
      rawPerformers: [],
      uuid: createUUID(),
      requireCompletionByAll: true,
      conditions: getEmptyConditions(isSubscribed),
      rawDueDate: createEmptyDueDate(),
      checklists: [],
      ...templateTask,
    };
  };

  const getEmptyTemplate = () => {
    return {
      description: '',
      kickoff: getEmptyKickoff(),
      name: DEFAULT_TEMPLATE_NAME,
      tasks: [getNewTask({ name: 'First Step', number: 1 })],
      isActive: false,
      finalizable: false,
      templateOwners: getNormalizedTemplateOwners([authUser.id], isSubscribed, users),
      wfNameTemplate: '{{date}} — {{template-name}}',
    } as ITemplate;
  };

  const handleChangeTemplateField = (field: keyof ITemplate) => (value: ITemplate[keyof ITemplate]) => {
    const workflow = template;
    setTemplateStatus(ETemplateStatus.Saving);

    if (field === 'isActive') {
      const newWorkflow: ITemplate = {
        ...workflow,
        isActive: value as boolean,
      };

      setTemplate(newWorkflow);
      submitDebounced();

      return;
    }

    const newWorkflow: ITemplate = {
      ...workflow,
      [field]: value,
      isActive: false,
    };

    setTemplate(newWorkflow);
    submitDebounced();
  };

  const handleChangeTextField = (field: keyof ITemplate) => (value: string) => handleChangeTemplateField(field)(value);

  const changeTasks = (newTasks: ITemplateTask[]) => {
    handleChangeTemplateField('tasks')(newTasks);
  };

  const handleRemoveTask = (targetTask: ITemplateTask) => () => {
    const newTasks = tasks
      .filter((task) => task.uuid !== targetTask.uuid)
      .map((task, index) => ({ ...task, number: index + 1 }));

    if (!isArrayWithItems(newTasks)) {
      changeTasks([getNewTask()]);

      return;
    }

    changeTasks(newTasks);
  };

  const handleAddTask = () => {
    if (!isArrayWithItems(tasks)) {
      const newTasks = [getNewTask()];

      changeTasks(newTasks);

      return;
    }

    const newTaskNumber = tasks.length + 1;
    const newTask = getNewTask({ number: newTaskNumber, name: `New Step ${newTaskNumber}` });
    const newTasks = [...tasks, newTask];

    toggleIsOpenTask(newTask.uuid);
    changeTasks(newTasks);
  };

  const getTasksWithNewTask = (newTask: ITemplateTask, newTaskIndex: number) => {
    const newTasks = [...tasks.slice(0, newTaskIndex), newTask, ...tasks.slice(newTaskIndex)].map((task, index) => ({
      ...task,
      number: index + 1,
    }));

    return newTasks;
  };

  const handleCloneTask = (targetTask: ITemplateTask) => () => {
    const newTask = getClonedTask(targetTask);
    const newTasks = getTasksWithNewTask(newTask, targetTask.number);
    changeTasks(newTasks);
    toggleIsOpenTask(newTask.uuid);
  };

  const handleAddTaskBefore = (targetTask: ITemplateTask) => () => {
    const newTaskName = `New Step ${tasks.length + 1}`;
    const newTask = getNewTask({ name: newTaskName });
    const newTasks = getTasksWithNewTask(newTask, targetTask.number - 1);

    changeTasks(newTasks);
    toggleIsOpenTask(newTask.uuid);
  };

  const toggleIsOpenTask = (taskUUID: string) => {
    const isTaskOpen = Boolean(openedTasks[taskUUID]);

    setOpenedTasks({ ...openedTasks, [taskUUID]: !isTaskOpen });
  };

  const handleMoveTask = (from: number, direction: EMoveDirections) => () => {
    const to = direction === EMoveDirections.Up ? from - 1 : from + 1;
    const movedTasks = moveTask(from, to, tasks);
    const sortedTasksLocal = [...movedTasks].sort((a, b) => a.number - b.number);

    changeTasks(sortedTasksLocal);
  };

  const handleEditTaskField =
    (targetTask: ITemplateTask) => (field: keyof ITemplateTask) => (value: ITemplateTask[keyof ITemplateTask]) => {
      const newTasks = tasks.map((task) => {
        if (targetTask.uuid === task.uuid) {
          return {
            ...targetTask,
            [field]: value,
          };
        }

        return task;
      });

      handleChangeTemplateField('tasks')(newTasks);
    };

  const addDelay = (targetTask: ITemplateTask) => () => {
    if (targetTask.delay) {
      const message = formatMessage({ id: 'template.delay-task-has-delay-error' });
      NotificationManager.warning({ message });

      return;
    }

    if (targetTask.number === 1) {
      const message = formatMessage({ id: 'template.delay-first-task-delay-error' });
      NotificationManager.warning({ message });

      return;
    }

    const newTasks = tasks.map((task) => {
      if (task.uuid === targetTask.uuid) {
        return {
          ...task,
          delay: EMPTY_DURATION,
        };
      }

      return task;
    });

    toggleDelay(targetTask.uuid);
    changeTasks(newTasks);
  };

  const editDelay = (targetTask: ITemplateTask) => (delay: string) => {
    const newTasks = tasks.map((task) => {
      if (task.uuid === targetTask.uuid) {
        return { ...targetTask, delay };
      }

      return task;
    });

    changeTasks(newTasks);
  };

  const deleteDelay = (targetTask: ITemplateTask) => () => {
    if (!targetTask.delay) {
      return;
    }

    handleEditTaskField(targetTask)('delay')('');
  };

  const toggleDelay = (taskUUID: string) => {
    const isDelayOpen = Boolean(openedDelays[taskUUID]);

    setOpenedDelays({ ...openedDelays, [taskUUID]: !isDelayOpen });
  };

  const submitDebounced = debounce(350, saveTemplate);

  const getTaskListItem = (task: ITemplateTask, index: number, tasksLocal: ITemplateTask[]) => {
    const isTaskOpen = Boolean(openedTasks[task.uuid]);
    const isDelayOpen = Boolean(openedDelays[task.uuid]);

    return (
      <TemplateEntity
        key={`template-entity-${task.uuid}`}
        index={index}
        task={task}
        users={users}
        tasksCount={tasksLocal.length}
        isSubscribed={isSubscribed}
        removeTask={handleRemoveTask(task)}
        cloneTask={handleCloneTask(task)}
        addDelay={addDelay(task)}
        addTaskBefore={handleAddTaskBefore(task)}
        deleteDelay={deleteDelay}
        editDelay={editDelay(task)}
        isTaskOpen={isTaskOpen}
        isDelayOpen={isDelayOpen}
        toggleDelay={() => toggleDelay(task.uuid)}
        handleMoveTask={handleMoveTask}
        toggleIsOpenTask={() => toggleIsOpenTask(task.uuid)}
      />
    );
  };

  const handleSetInfoWarnings = (infoWarningsLocal: ((props: IInfoWarningProps) => JSX.Element)[]) => {
    if (isArrayWithItems(infoWarningsLocal)) {
      setIsInfoWarningsModaOpen(true);
      setInfoWarnings(infoWarningsLocal);
    }
  };

  const renderInfoWarningsModal = () => {
    const handleCloseModal = () => setIsInfoWarningsModaOpen(false);

    return <InfoWarningsModal isOpen={isInfoWarningsModaOpen} onClose={handleCloseModal} warnings={infoWarnings} />;
  };

  if (templateStatus === ETemplateStatus.Loading) {
    return <div className="loading" />;
  }

  return (
    <div className={styles['container']}>
      {renderInfoWarningsModal()}

      <AutoSaveStatusContainer onRetry={saveTemplate} />

      <div className={styles['template-wrapper']}>
        <div className={styles['template-wrapper__info']}>
          <StickyBox offsetTop={NAVBAR_HEIGHT} offsetBottom={20}>
            <EditableText
              text={templateName}
              className={styles['template-name']}
              onChangeText={handleChangeTextField('name')}
              placeholder={formatMessage({ id: 'template.name-placeholder' })}
              editButtonHint={formatMessage({ id: 'template.edit-name' })}
            />
            <div className={styles['description']}>
              <TextareaAutosize
                placeholder={formatMessage({ id: 'template.placeholder' })}
                className={classnames('form-control', styles['textarea'], styles['form-control-locall'])}
                onChange={(e) => handleChangeTextField('description')(e.target.value)}
                value={templateDescription}
              />
            </div>

            <TemplateControllsContainer setInfoWarnings={handleSetInfoWarnings} />

            {(updatedBy || dateUpdated) && (
              <div className={styles['last-update']}>
                <TemplateLastUpdateInfo updatedBy={updatedBy} dateUpdated={dateUpdated} />
              </div>
            )}
          </StickyBox>
        </div>
        <div className={styles['template-wrapper__tasks']}>
          <ConditionsBanner />
          <div className={styles['tasks']}>
            <div className={styles['kickoff-wrapper']}>
              <KickoffReduxContainer setKickoff={handleChangeTemplateField('kickoff')} />
            </div>
            {sortedTasks().map(getTaskListItem)}
            <AddEntityButton
              entities={[
                {
                  title: EEntityTitle.Task,
                  onAddEntity: handleAddTask,
                },
              ]}
            />
            <TemplateIntegrations />
          </div>
        </div>
      </div>
    </div>
  );
}

export interface ITemplateEditProps {
  match: any;
  location: any;
  authUser: IAuthUser;
  template: ITemplate;
  aiTemplate: ITemplate | null;
  templateStatus: ETemplateStatus;
  users: TUserListItem[];
  isSubscribed: boolean;
  loadTemplate(id: number): void;
  loadTemplateFromSystem(id: string): void;
  resetTemplateStore(): void;
  saveTemplate(): void;
  setTemplate(payload: ITemplate): void;
  setTemplateStatus(status: ETemplateStatus): void;
  loadTemplateVariablesSuccess(payload: TLoadTemplateVariablesSuccessPayload): void;
}

export type TTemplateEditProps = ITemplateEditProps & RouteComponentProps;

export interface ITemplateEditParams {
  id: string;
}

export interface ITemplateEditState {
  isInfoWarningsModaOpen: boolean;
  infoWarnings: ((props: IInfoWarningProps) => JSX.Element)[];
  openedTasks: { [key: string]: boolean };
  openedDelays: { [key: string]: boolean };
}
