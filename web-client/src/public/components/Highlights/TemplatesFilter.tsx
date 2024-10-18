/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { Checkbox } from '../UI/Fields/Checkbox';
import { IntlMessages } from '../IntlMessages';
import { isArrayWithItems } from '../../utils/helpers';
import { ShowMore } from '../UI/ShowMore';
import { ITemplateTitle } from '../../types/template';

import styles from './Filters.css';

export interface ITemplatesFilterProps {
  searchText: string;
  selectedTemplates: number[];
  templatesTitles: ITemplateTitle[];
  isFiltersLoading: boolean;
  changeTemplatesSearchText(e: React.ChangeEvent<HTMLInputElement>): void;
  changeTemplatesFilter(templateId: number): (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const MAX_SHOW_TEMPLATES = 10;

export function TemplatesFilter({
  searchText,
  selectedTemplates,
  templatesTitles,
  isFiltersLoading,
  changeTemplatesSearchText,
  changeTemplatesFilter,
}: ITemplatesFilterProps) {
  const { useCallback, useEffect, useMemo, useState } = React;
  const { formatMessage } = useIntl();

  const isEmpty = !isArrayWithItems(templatesTitles);

  const renderWorkflowsPlaceholder = () => {
    if (!isEmpty) {
      return null;
    }

    return (
      <p className={styles['workflows-filter__placeholder']}>
        <IntlMessages id="workflow-highlights.no-processes-started" />
      </p>
    );
  };

  const isTemplatesNumberExceeded = useMemo(
    () => templatesTitles.length > MAX_SHOW_TEMPLATES,
    [templatesTitles],
  );

  const isSearchFilled = useMemo(
    () => searchText.length > 1,
    [searchText],
  );

  const [isShowAllVisibleState, setShowAllVisibleState] = useState(isTemplatesNumberExceeded);

  useEffect(
    () => setShowAllVisibleState(isSearchFilled ? false : isTemplatesNumberExceeded),
    [isTemplatesNumberExceeded, isSearchFilled],
  );

  const handleShowAll = useCallback(
    () => setShowAllVisibleState(!isShowAllVisibleState),
    [isShowAllVisibleState],
  );

  const truncatedTemplates = useMemo(() => {
    if (!isShowAllVisibleState && !isSearchFilled) {
      return templatesTitles;
    }

    if (isSearchFilled) {
      return templatesTitles.filter(({ name }) => name.toLowerCase().includes(searchText.toLowerCase()));
    }

    const templatesToShow = templatesTitles.slice(0, MAX_SHOW_TEMPLATES);
    const isSelectedWorkflowsHidden = selectedTemplates.some(id => !templatesToShow.map(({ id }) => id).includes(id));

    if (isSelectedWorkflowsHidden) {
      handleShowAll();
    }

    return templatesToShow;
  }, [isShowAllVisibleState, searchText, selectedTemplates, templatesTitles]);

  const isPanelExpanded = isArrayWithItems(selectedTemplates) ? true : undefined;
  const lastCheckboxClassname = isShowAllVisibleState ? styles['mb-1'] : styles['mb-4'];

  return (
    <ShowMore
      containerClassName={styles['filter-container']}
      label="process-highlights.date-picker-by-template-label"
      isInitiallyVisible={isPanelExpanded}
    >
      {renderWorkflowsPlaceholder()}
      {isTemplatesNumberExceeded &&
        <input
          className={styles['filter__input']}
          disabled={isFiltersLoading}
          placeholder={formatMessage({ id: 'process-highlights.search-workflows-placeholder' })}
          value={searchText}
          onChange={changeTemplatesSearchText}
          autoFocus
        />
      }
      {isFiltersLoading && <div className={classnames('loading', styles['filter__spinner'])} />}
      <div
        className={classnames(
          styles['filter__checkboxes'],
          isFiltersLoading && styles['filter__checkboxes_disabled'],
        )}
      >
        {truncatedTemplates.map((template, idx) => (
          <Checkbox
            key={template.id}
            containerClassName={idx === templatesTitles.length - 1 ? lastCheckboxClassname : styles['mb-1']}
            id={`workflows-filter__checkbox_${template.name}`}
            title={template.name}
            onChange={changeTemplatesFilter(template.id)}
            checked={selectedTemplates.includes(template.id)}
          />
        ))}
      </div>
      {isShowAllVisibleState &&
        <button
          className={classnames('mb-4', styles['filter__button-show-all'])}
          onClick={handleShowAll}
          disabled={isFiltersLoading}
        >
          <IntlMessages id="process-highlights.show-all-workflows" />
        </button>
      }
    </ShowMore>
  );
}
