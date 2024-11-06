/* eslint-disable react/button-has-type */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import classnames from 'classnames';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';
import { Link } from 'react-router-dom';
import { debounce } from 'throttle-debounce';

import { ETaskListStatus } from './types';
import { TasksPlaceholderIcon } from './TasksPlaceholderIcon';

import { ERoutes } from '../../constants/routes';
import { useCheckDevice } from '../../hooks/useCheckDevice';
import { ETaskListCompleteSorting, ETaskListCompletionStatus, ETaskListSorting, ITask } from '../../types/tasks';
import { TITLES } from '../../constants/titles';
import { ITaskList } from '../../types/redux';
import { ETaskCardViewMode, TaskCardContainer } from '../TaskCard';
import { TaskPreviewCardSkeleton } from './Skeletons';
import { TaskPreviewCard } from './TaskPreviewCard';
import { TLoadCurrentTaskPayload } from '../../redux/actions';
import { history } from '../../utils/history';
import { getTaskDetailRoute } from '../../utils/routes';
import { TaskCarkSkeleton } from '../TaskCard/TaskCarkSkeleton';
import { Button, InputField, Placeholder } from '../UI';
import { useDidUpdateEffect } from '../../hooks/useDidUpdateEffect';
import { EPageTitle } from '../../constants/defaultValues';
import { PageTitle } from '../PageTitle/PageTitle';

import styles from './Tasks.css';

export interface ITasksProps {
  isAdmin: boolean;
  taskList: ITaskList;
  taskSorting: ETaskListSorting | ETaskListCompleteSorting;
  completionStatus: ETaskListCompletionStatus;
  templateIdFilter: number | null;
  stepIdFilter: number | null;
  taskListStatus: ETaskListStatus;
  detailedTaskId: number | null;
  detailedTask: ITask | null;
  withPaywall: boolean;
  hasNewTasks: boolean;
  searchText: string;
  loadDetailedTask(payload: TLoadCurrentTaskPayload): void;
  setDetailedTaskId(id: number): void;
  loadTaskList(value: number): void;
  resetTasks(): void;
  changeSearchText(text: string): void;
  showNewTasksNotification(value: boolean): void;
  openSelectTemplateModal(): void;
  searchTasks(): void;
}

const LOADERS_QUANTITY = 2;

export function Tasks({
  isAdmin,
  taskListStatus,
  detailedTaskId,
  taskList: { count, items },
  withPaywall,
  detailedTask,
  hasNewTasks,
  taskSorting,
  templateIdFilter,
  stepIdFilter,
  searchText,
  completionStatus,
  loadTaskList,
  loadDetailedTask,
  setDetailedTaskId,
  resetTasks,
  changeSearchText,
  showNewTasksNotification,
  openSelectTemplateModal,
  searchTasks,
}: ITasksProps) {
  const { formatMessage } = useIntl();

  const [searchQuery, setSearchQuery] = useState(searchText);

  const isListFullLoaded = useMemo(() => count === items.length, [count, items]);
  const { isMobile } = useCheckDevice();

  const debounceChangeSearchText = useCallback(debounce(500, changeSearchText), []);

  useEffect(() => {
    debounceChangeSearchText(searchQuery);
  }, [searchQuery]);

  useEffect(() => {
    document.title = TITLES.Tasks;
    loadTaskList(0);

    return () => {
      resetTasks();
    };
  }, []);

  useDidUpdateEffect(() => {
    searchTasks();
  }, [taskSorting, templateIdFilter, stepIdFilter, completionStatus, searchText]);

  useEffect(() => {
    if (hasNewTasks) {
      showNewTasksNotification(false);
    }
  }, [hasNewTasks]);

  useEffect(() => {
    const isActiveFirst = items[0]?.id === detailedTaskId;
    if (isActiveFirst) {
      document.getElementById('scrollableDiv')?.scroll(0, 0);
    }
  }, [detailedTaskId]);

  const loader = (
    <div className={styles['cards__inner']}>
      {Array.from(Array(LOADERS_QUANTITY), (_, index) => (
        <div key={index} className={styles['cards__item']}>
          <TaskPreviewCardSkeleton key={index} />
        </div>
      ))}
    </div>
  );

  const renderCurrentTask = () => {
    const isLoading = taskListStatus === ETaskListStatus.Loading || taskListStatus === ETaskListStatus.Searching;
    if (isLoading && !detailedTask) {
      return <TaskCarkSkeleton />;
    }

    return <TaskCardContainer viewMode={ETaskCardViewMode.List} />;
  };

  const renderPlaceholder = () => {
    if (taskListStatus === ETaskListStatus.WaitingForAction) {
      return null;
    }

    if (taskListStatus === ETaskListStatus.NoTasks) {
      const placeholderFooter = (
        <div className={styles['placeholder-footer']}>
          <Button
            type="button"
            size="sm"
            buttonStyle="yellow"
            label={formatMessage({ id: 'tasks.emply-tasks-placeholder-run-workflow' })}
            onClick={openSelectTemplateModal}
            className={styles['placeholder-footer__run-workflow']}
          />
          {/* <button className="cancel-button"> */}
          <Link className={styles['placeholder__link']} to={ERoutes.TemplatesCreate}>
            {formatMessage({ id: 'tasks.emply-tasks-placeholder-new-template' })}
          </Link>
          {/* </button> */}
        </div>
      );

      return (
        <Placeholder
          title={formatMessage({ id: 'tasks.emply-tasks-placeholder-title' })}
          description={
            isAdmin
              ? formatMessage({ id: 'tasks.emply-tasks-placeholder-description' })
              : formatMessage({ id: 'tasks.emply-tasks-placeholder-description-non-admin' })
          }
          Icon={TasksPlaceholderIcon}
          mood="neutral"
          footer={isAdmin && placeholderFooter}
          containerClassName={styles['placeholder']}
        />
      );
    }

    if (taskListStatus === ETaskListStatus.EmptySearchResult) {
      return (
        <Placeholder
          title={formatMessage({ id: 'tasks.emply-search-placeholder-title' })}
          description={formatMessage({ id: 'tasks.emply-search-placeholder-description' })}
          Icon={TasksPlaceholderIcon}
          mood="bad"
          containerClassName={styles['placeholder']}
        />
      );
    }

    if (taskListStatus === ETaskListStatus.LastTaskFinished) {
      return (
        <Placeholder
          title={formatMessage({ id: 'tasks.success-placeholder-title' })}
          description={formatMessage({ id: 'tasks.success-placeholder-description' })}
          Icon={TasksPlaceholderIcon}
          mood="good"
          footer={
            <Link className="cancel-button" to={ERoutes.Main}>
              {formatMessage({ id: 'tasks.success-placeholder-link' })}
            </Link>
          }
          containerClassName={styles['placeholder']}
        />
      );
    }

    if (taskListStatus === ETaskListStatus.LastFilteredTaskFinished) {
      return (
        <Placeholder
          title={formatMessage({ id: 'tasks.emply-search-placeholder-title' })}
          description={formatMessage({ id: 'tasks.emply-search-placeholder-description' })}
          Icon={TasksPlaceholderIcon}
          mood="neutral"
          containerClassName={styles['placeholder']}
        />
      );
    }

    return null;
  };

  const renderTasksList = () => {
    if (taskListStatus === ETaskListStatus.Searching) {
      return <div className={styles['cards']}>{loader}</div>;
    }

    return (
      <div className={styles['cards']} id="scrollableDiv">
        <InfiniteScroll
          dataLength={items.length}
          next={() => loadTaskList(items.length)}
          loader={loader}
          hasMore={!isListFullLoaded || taskListStatus === ETaskListStatus.Loading}
          {...(!isMobile && { scrollableTarget: 'scrollableDiv' })}
        >
          {items.map((task) => (
            <div key={task.id} className={styles['cards__item']}>
              <TaskPreviewCard
                task={task}
                completionStatus={completionStatus}
                isActive={!isMobile && task.id === detailedTaskId}
                onClick={hanldeOpenDetailedTask(task.id)}
              />
            </div>
          ))}
        </InfiniteScroll>
      </div>
    );
  };

  const renderTasks = () => {
    return (
      <>
        <div className={styles['left-area']}>
          <div
            className={classnames(styles['left-area__inner'], withPaywall && styles['left-area__inner_with-paywall'])}
          >
            <PageTitle withUnderline={false} titleId={EPageTitle.MyTasks} mbSize="sm" />
            <InputField
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.currentTarget.value)}
              className={styles['search-field']}
              placeholder="Search Tasks"
              onClear={() => setSearchQuery('')}
            />
            {renderTasksList()}
          </div>
        </div>
        <div className={styles['right-area']}>
          {renderPlaceholder()}

          <div className={styles['task']}>{renderCurrentTask()}</div>
        </div>
      </>
    );
  };

  const hanldeOpenDetailedTask = (taskId: number) => () => {
    if (isMobile) {
      const redirectUrl = getTaskDetailRoute(taskId);
      history.push(redirectUrl);

      return;
    }

    setDetailedTaskId(taskId);
    loadDetailedTask({ taskId });
  };

  return <div className={classnames(styles['container'])}>{renderTasks()}</div>;
}
