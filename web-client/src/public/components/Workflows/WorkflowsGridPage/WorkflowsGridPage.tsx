// tslint:disable-next-line: match-default-export-name
import React, { useCallback, useEffect, useState } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import StickyBox from 'react-sticky-box';
import { debounce } from 'throttle-debounce';

import { Header } from '../../UI/Typeography/Header';
import { isArrayWithItems } from '../../../utils/helpers';
import { EPageTitle, NAVBAR_HEIGHT } from '../../../constants/defaultValues';
import { SearchLargeIcon, StartRoundIcon } from '../../icons';
import { getTemplate } from '../../../api/getTemplate';
import { getRunnableWorkflow } from '../../TemplateEdit/utils/getRunnableWorkflow';
import { logger } from '../../../utils/logger';
import { NotificationManager } from '../../UI/Notifications';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import { InputField, Loader } from '../../UI';
import { PageTitle } from '../../PageTitle/PageTitle';
import { IWorkflowsProps } from '../types';
import { EWorkflowsLoadingStatus } from '../../../types/workflow';

import { WorkflowCardContainer } from './WorkflowCard';
import { WorkflowCardLoader } from './WorkflowCardLoader';
import { WorkflowsFiltersContainer } from './WorkflowsFilters';

import styles from './WorkflowsGridPage.css';

export const WorkflowsGridPage = React.memo(function Workflows({
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

  const [searchQuery, setSearchQuery] = useState(searchText);
  const [isRunningNewWorkflow, setIsRunningNewWorkflow] = useState(false);

  const debounceOnSearch = useCallback(debounce(500, onSearch), []);

  useEffect(() => {
    debounceOnSearch(searchQuery);
  }, [searchQuery]);

  const handleOpenPopup = (workflowId: number) => () => {
    openWorkflowLogPopup({ workflowId, shouldSetWorkflowDetailUrl: true, redirectTo404IfNotFound: true });
  };

  React.useEffect(() => {
    if (workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList && stepsIdsFilter.length) {
      setStepsFilter([]);
    }
  }, [workflowsLoadingStatus]);

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
      NotificationManager.error({ message: getErrorMessage(error) });
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
        <StartRoundIcon />
        <Header size="6" tag="p" className={styles['run-workflow-card__text']}>
          {templatesFilter.length !== 1
            ? formatMessage({ id: 'workflows.run-workflow' })
            : `${formatMessage({ id: 'workflows.run-workflows' })} ${templatesFilter
              .map((t) => t.name)
              .join(', ')
              .trim()}`}
        </Header>
      </button>
    );
  };

  const renderContent = () => {
    if (workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList) {
      const INIT_SKELETION_QUANTITY = 16;
      const loader = Array(INIT_SKELETION_QUANTITY).fill(<WorkflowCardLoader />);

      return <div className={styles['cards']}>{loader}</div>;
    }

    const SCROLL_LOADERS_QUANTITY = 2;
    const isListFullLoaded =
      count === items.length && workflowsLoadingStatus !== EWorkflowsLoadingStatus.LoadingNextPage;
    const loader = Array(SCROLL_LOADERS_QUANTITY).fill(<WorkflowCardLoader />);

    return (
      <InfiniteScroll
        dataLength={items.length}
        next={() => loadWorkflowsList(items.length)}
        loader={loader}
        hasMore={!isListFullLoaded}
        className={styles['cards']}
      >
        {renderRunWorkflowButton()}
        {items.map((item) => (
          <WorkflowCardContainer
            key={item.id}
            workflow={item}
            onCardClick={handleOpenPopup(item.id)}
            onWorkflowEnded={() => removeWorkflowFromList({ workflowId: item.id })}
            onWorkflowSnoozed={() => removeWorkflowFromList({ workflowId: item.id })}
            onWorkflowDeleted={() => removeWorkflowFromList({ workflowId: item.id })}
            onWorkflowResumed={() => removeWorkflowFromList({ workflowId: item.id })}
          />
        ))}
      </InfiniteScroll>
    );
  };

  return (
    <div className={styles['container']}>
      <div className={styles['filters']}>
        <StickyBox offsetTop={NAVBAR_HEIGHT} offsetBottom={20}>
          <PageTitle titleId={EPageTitle.Workflows} className={styles['title']} withUnderline={false} />
          <WorkflowsFiltersContainer />
        </StickyBox>
      </div>

      <div className={styles['content']}>
        <div className={styles['search']}>
          <SearchLargeIcon className={styles['search__icon']} />
          <InputField
            value={searchQuery}
            onChange={e => setSearchQuery(e.currentTarget.value)}
            containerClassName={styles['search-field']}
            className={styles['search-field__input']}
            placeholder={formatMessage({ id: 'workflows.search' })}
            fieldSize="md"
            onClear={() => setSearchQuery('')}
          />
        </div>

        {renderContent()}
      </div>
    </div>
  );
});
