import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { Checkbox } from '../UI/Fields/Checkbox';
import { IntlMessages } from '../IntlMessages';
import { isArrayWithItems } from '../../utils/helpers';
import { ShowMore } from '../UI/ShowMore';
import { ITemplatesFilterProps } from './types';

import styles from './Filters.css';

const MAX_SHOW_TEMPLATES = 10;

export function TemplatesFilter({
  searchText,
  selectedTemplates,
  templatesTitles,
  isFiltersLoading,
  changeTemplatesSearchText,
  changeTemplatesFilter,
}: ITemplatesFilterProps) {
  const { formatMessage } = useIntl();
  const hasFocusedSearchRef = useRef(false);

  const isEmpty = !isArrayWithItems(templatesTitles);

  const renderWorkflowsPlaceholder = () => {
    if (!isEmpty) {
      return null;
    }

    return (
      <p className={styles['filter__placeholder']}>
        <IntlMessages id="workflow-highlights.no-processes-started" />
      </p>
    );
  };

  const isTemplatesNumberExceeded = useMemo(() => templatesTitles.length > MAX_SHOW_TEMPLATES, [templatesTitles]);

  const isSearchFilled = useMemo(() => searchText.length > 1, [searchText]);

  const [isShowAllVisibleState, setShowAllVisibleState] = useState(isTemplatesNumberExceeded);

  const setSearchInputRef = useCallback((node: HTMLInputElement | null) => {
    if (!node || hasFocusedSearchRef.current || isFiltersLoading) {
      return;
    }

    node.focus();
    hasFocusedSearchRef.current = true;
  }, [isFiltersLoading]);

  useEffect(() => {
    setShowAllVisibleState(isSearchFilled ? false : isTemplatesNumberExceeded);
  }, [isTemplatesNumberExceeded, isSearchFilled]);

  const handleShowAll = useCallback(() => {
    setShowAllVisibleState((isVisible) => !isVisible);
  }, []);

  const truncatedTemplates = useMemo(() => {
    if (!isShowAllVisibleState && !isSearchFilled) {
      return templatesTitles;
    }

    if (isSearchFilled) {
      return templatesTitles.filter(({ name }) => name.toLowerCase().includes(searchText.toLowerCase()));
    }

    const templatesToShow = templatesTitles.slice(0, MAX_SHOW_TEMPLATES);
    const isSelectedWorkflowsHidden = selectedTemplates.some(
      (templateId) => !templatesToShow.map(({ id }) => id).includes(templateId),
    );

    if (isSelectedWorkflowsHidden) {
      handleShowAll();
    }

    return templatesToShow;
  }, [handleShowAll, isSearchFilled, isShowAllVisibleState, searchText, selectedTemplates, templatesTitles]);

  const isPanelExpanded = isArrayWithItems(selectedTemplates) ? true : undefined;

  return (
    <ShowMore
      containerClassName={styles['filter']}
      label="process-highlights.date-picker-by-template-label"
      isInitiallyVisible={isPanelExpanded}
    >
      {renderWorkflowsPlaceholder()}
      {isTemplatesNumberExceeded && (
        <input
          ref={setSearchInputRef}
          className={styles['filter__input']}
          disabled={isFiltersLoading}
          placeholder={formatMessage({ id: 'process-highlights.search-workflows-placeholder' })}
          value={searchText}
          onChange={changeTemplatesSearchText}
        />
      )}
      {isFiltersLoading && <div className={classnames('loading', styles['filter__spinner'])} />}
      <div
        className={classnames(
          styles['filter__options'],
          isFiltersLoading && styles['filter__options--disabled'],
        )}
      >
        {truncatedTemplates.map((template) => (
          <Checkbox
            key={template.id}
            id={`workflows-filter__checkbox_${template.name}`}
            title={template.name}
            titleClassName={styles['filter__option-label']}
            labelClassName={styles['filter__option-row']}
            onChange={changeTemplatesFilter(template.id)}
            checked={selectedTemplates.includes(template.id)}
          />
        ))}
      </div>
      {isShowAllVisibleState && (
        <button
          type="button"
          className={styles['filter__show-all']}
          onClick={handleShowAll}
          disabled={isFiltersLoading}
          aria-label={formatMessage({ id: 'process-highlights.show-all-workflows' })}
        >
          <IntlMessages id="process-highlights.show-all-workflows" />
        </button>
      )}
    </ShowMore>
  );
}
