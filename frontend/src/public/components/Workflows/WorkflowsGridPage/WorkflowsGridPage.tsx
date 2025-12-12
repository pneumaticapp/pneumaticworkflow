/* eslint-disable indent */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { debounce } from 'throttle-debounce';

import { Header } from '../../UI/Typeography/Header';
import { isArrayWithItems } from '../../../utils/helpers';
import { EPageTitle } from '../../../constants/defaultValues';
import { SearchLargeIcon, StartRoundIcon } from '../../icons';
import { getTemplate } from '../../../api/getTemplate';
import { getRunnableWorkflow } from '../../TemplateEdit/utils/getRunnableWorkflow';
import { logger } from '../../../utils/logger';
import { NotificationManager } from '../../UI/Notifications';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import {
  InputField,
  Loader,
  //  Placeholder
} from '../../UI';
import { PageTitle } from '../../PageTitle/PageTitle';
import { IWorkflowsProps } from '../types';
import { EWorkflowsLoadingStatus } from '../../../types/workflow';

import { WorkflowCardContainer } from './WorkflowCard';
import { WorkflowCardLoader } from './WorkflowCardLoader';

import styles from './WorkflowsGridPage.css';
// import { createWorkflowsPlaceholderIcon } from '../WorkflowsPlaceholderIcon';
// import { useCheckDevice } from '../../../hooks/useCheckDevice';

const useSearchWithDebounce = (initialSearchText: string, onSearch: (query: string) => void, debounceTime = 800) => {
  const [searchQuery, setSearchQuery] = useState(initialSearchText);
  const isFirstSearch = useRef(true);
  const debouncedSearch = useCallback(debounce(debounceTime, onSearch), []);

  useEffect(() => {
    if (searchQuery.length === 0) {
      onSearch(searchQuery);
      return;
    }

    if (isFirstSearch.current) {
      isFirstSearch.current = false;
      onSearch(searchQuery);
    } else {
      debouncedSearch(searchQuery);
    }
  }, [searchQuery]);

  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  return { searchQuery, handleSearch } as const;
};

export const WorkflowsGridPage = function Workflows({
  workflowsLoadingStatus,
  workflowsList: { count, items },
  templatesFilter,
  searchText,
  stepsIdsFilter,
  onSearch,
  setStepsFilter,
  loadWorkflowsList,
  openWorkflowLogPopup,
  openSelectTemplateModal,
  openRunWorkflowModal,
  removeWorkflowFromList,
}: IWorkflowsProps) {
  const { formatMessage } = useIntl();
  const { searchQuery, handleSearch } = useSearchWithDebounce(searchText, onSearch);
  const [isRunningNewWorkflow, setIsRunningNewWorkflow] = useState(false);
  // const { isMobile } = useCheckDevice();

  React.useEffect(() => {
    if (workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList && stepsIdsFilter.length) {
      setStepsFilter([]);
    }
  }, [workflowsLoadingStatus]);

  const handleOpenPopup = (workflowId: number) => () => {
    openWorkflowLogPopup({ workflowId, shouldSetWorkflowDetailUrl: true, redirectTo404IfNotFound: true });
  };

  const handleRunNewWorkflow = async () => {
    if (!isArrayWithItems(templatesFilter)) {
      openSelectTemplateModal();

      return;
    }

    if (templatesFilter.length > 1) {
      openSelectTemplateModal({ templatesIdsFilter: templatesFilter.map((t) => t.id) });

      return;
    }

    try {
      setIsRunningNewWorkflow(true);
      const [{ id: templateId }] = templatesFilter;
      const template = await getTemplate(templateId);
      if (!template) {
        openSelectTemplateModal();

        return;
      }
      const runnableWorkflow = getRunnableWorkflow(template);
      if (!runnableWorkflow) {
        openSelectTemplateModal();

        return;
      }
      openRunWorkflowModal(runnableWorkflow);
    } catch (error) {
      logger.error('failed to run new workflow', error);
      NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
    } finally {
      setIsRunningNewWorkflow(false);
    }
  };

  const renderRunWorkflowButton = () => {
    return (
      <button
        type="button"
        onClick={handleRunNewWorkflow}
        className={classnames(styles['card-wrapper'], styles['run-workflow-card'])}
      >
        <Loader isLoading={isRunningNewWorkflow} />

        <Header size="6" tag="p" className={styles['run-workflow-card__text']}>
          {templatesFilter.length !== 1
            ? formatMessage({ id: 'workflows.run-workflow' })
            : `${formatMessage({ id: 'workflows.run-workflows' })} ${templatesFilter
                .map((t) => t.name)
                .join(', ')
                .trim()}`}
        </Header>
        {templatesFilter.length !== 1 && (
          <div className={styles['run-workflow-card__extra-text']}>
            {formatMessage({ id: 'workflows.run-workflow-extra-text' })}
          </div>
        )}
        <StartRoundIcon className={styles['run-workflow-card__icon']} />
      </button>
    );
  };

  const renderContent = () => {
    if (workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList) {
      const INIT_SKELETION_QUANTITY = 16;
      const loader = Array(INIT_SKELETION_QUANTITY).map((item) => <WorkflowCardLoader key={item} />);

      return <div className={styles['cards']}>{loader}</div>;
    }

    const SCROLL_LOADERS_QUANTITY = 2;
    const isListFullLoaded =
      count === items.length && workflowsLoadingStatus !== EWorkflowsLoadingStatus.LoadingNextPage;
    const loader = Array(SCROLL_LOADERS_QUANTITY).map((item) => <WorkflowCardLoader key={item} />);

    return (
      <InfiniteScroll
        dataLength={items.length}
        next={() => loadWorkflowsList(items.length)}
        loader={loader}
        hasMore={!isListFullLoaded}
        className={styles['cards']}
        scrollableTarget="app-container"
      >
        {renderRunWorkflowButton()}
        {/* {items.length !== 0 ? (
          renderRunWorkflowButton()
        ) : (
          <Placeholder
            title={formatMessage({ id: 'workflows.empty-placeholder-title' })}
            description={formatMessage({ id: 'workflows.empty-placeholder-description' })}
            Icon={() => createWorkflowsPlaceholderIcon(isMobile)}
            containerClassName={styles['empty-list-placeholder-container']}
          />
        )} */}
        {items.map((item) => (
          <WorkflowCardContainer
            key={item.id}
            workflow={item}
            onCardClick={handleOpenPopup(item.id)}
            onWorkflowEnded={() => loadWorkflowsList(0)}
            onWorkflowDeleted={() => removeWorkflowFromList({ workflowId: item.id })}
          />
        ))}
      </InfiniteScroll>
    );
  };

  return (
    <div className={styles['container']}>
      <PageTitle titleId={EPageTitle.Workflows} className={styles['title']} withUnderline={false} />
      <div className={styles['content']}>
        <div className={styles['search']}>
          <SearchLargeIcon className={styles['search__icon']} />
          <InputField
            value={searchQuery}
            onChange={(e) => handleSearch(e.currentTarget.value)}
            containerClassName={styles['search-field']}
            className={styles['search-field__input']}
            placeholder={formatMessage({ id: 'workflows.search' })}
            fieldSize="md"
            onClear={() => handleSearch('')}
          />
        </div>

        {renderContent()}
      </div>
    </div>
  );
};
