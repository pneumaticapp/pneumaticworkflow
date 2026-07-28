import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { TeamUserSkeleton } from '../Team/TeamUserSkeleton';
import { TITLES } from '../../constants/titles';
import { PageTitle } from '../PageTitle';
import { EPageTitle } from '../../constants/defaultValues';
import { SearchLargeIcon } from '../icons';
import { InputField, Placeholder } from '../UI';
import { AddButton } from '../UI/Buttons/AddButton';
import { IAiAgent } from '../../redux/aiAgents/types';
import { loadAiAgents, openAiAgentModal } from '../../redux/actions';
import {
  getAiAgentsEnabled,
  getAiAgentsIsLoading,
  getAiAgentsList,
} from '../../redux/selectors/aiAgents';
import { TasksPlaceholderIcon } from '../Tasks/TasksPlaceholderIcon';
import { AiAgent } from './AiAgent';
import { AiAgentModal } from './AiAgentModal';

import styles from './AiAgents.css';

export function AiAgents() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const agents = useSelector(getAiAgentsList);
  const isLoading = useSelector(getAiAgentsIsLoading);
  const isEnabled = useSelector(getAiAgentsEnabled);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    dispatch(loadAiAgents());
    document.title = TITLES.AiAgents;
  }, []);

  const renderSearch = () => {
    return (
      <>
        <SearchLargeIcon className={styles['search__icon']} />
        <InputField
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          containerClassName={styles['search-field']}
          className={styles['search-field__input']}
          placeholder={formatMessage({ id: 'ai-agents.search' })}
          fieldSize="md"
          onClear={() => setSearchQuery('')}
        />
      </>
    );
  };

  const renderAgents = () => {
    if (isLoading) return Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);

    const getFilteredAgents = () => {
      if (!searchQuery) return agents;

      const queryWords = searchQuery.split(' ').map((str) => str.toLowerCase());
      const checkQueryWord = (queryWord: string, agent: IAiAgent) => {
        return [agent.name, agent.modelSlug]
          .map((str) => str.toLowerCase())
          .some((property) => property.includes(queryWord));
      };

      return agents.filter((agent) => {
        return queryWords.every((queryWord) => checkQueryWord(queryWord, agent));
      });
    };

    const filteredAgents = getFilteredAgents();

    if (!filteredAgents.length) {
      return (
        <Placeholder
          title={formatMessage({ id: 'ai-agents.empty-result-title' })}
          description={formatMessage({ id: 'ai-agents.empty-result-description' })}
          Icon={TasksPlaceholderIcon}
          mood="neutral"
          containerClassName={styles['placeholder']}
        />
      );
    }

    return filteredAgents.map((agent) => {
      return (
        <div key={agent.id} className={styles['agents__item']}>
          <AiAgent agent={agent} />
        </div>
      );
    });
  };

  if (!isEnabled && !isLoading) {
    return (
      <div className={styles['container']}>
        <PageTitle titleId={EPageTitle.AiAgents} withUnderline={false} />
        <Placeholder
          title={formatMessage({ id: 'ai-agents.disabled-title' })}
          description={formatMessage({ id: 'ai-agents.disabled-description' })}
          Icon={TasksPlaceholderIcon}
          mood="neutral"
          containerClassName={styles['placeholder']}
        />
      </div>
    );
  }

  return (
    <div className={styles['container']}>
      <PageTitle titleId={EPageTitle.AiAgents} withUnderline={false} />
      <section className={styles['search']}>{renderSearch()}</section>
      <AddButton
        title={formatMessage({ id: 'ai-agents.add-agent.title' })}
        caption={formatMessage({ id: 'ai-agents.add-agent.caption' })}
        onClick={() => dispatch(openAiAgentModal(null))}
      />
      <div className={styles['agents']}>{renderAgents()}</div>
      <AiAgentModal />
    </div>
  );
}

// eslint-disable-next-line no-restricted-exports
export default AiAgents;
