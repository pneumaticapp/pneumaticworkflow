import React, { useCallback, useEffect, useMemo, useState } from 'react';
import PerfectScrollbar from 'react-perfect-scrollbar';
import { useIntl } from 'react-intl';
import { debounce } from 'throttle-debounce';
import InfiniteScroll from 'react-infinite-scroll-component';

import { ITemplatesSystem, ITemplatesSystemCategories } from '../../../types/redux';
import { TemplateSystemCard } from '../TemplateSystemCard/TemplateSystemCard';
import { TemplateSystemCategoryItem } from '../TemplateSystemCategoryItem';
import { InputField, Placeholder } from '../../UI';
import { SearchLargeIcon } from '../../icons';
import { PageTitle } from '../../PageTitle/PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';
import { ISystemTemplate } from '../../../types/template';
import { TasksPlaceholderIcon } from '../../Tasks/TasksPlaceholderIcon';
import { TemplateSystemSkeleton } from '../TemplateSystemSkeleton';

import styles from '../Templates.css';
import { ETemplatesSystemStatus } from '../../../redux/actions';

const LOADERS_QUANTITY = 4;

export function TemplatesSystem({
  systemTemplates,
  changeTemplatesSystemSelectionSearch,
  changeTemplatesSystemSelectionCategory,
  changeTemplatesSystemPaginationNext,
}: ITemplatesSystemProps) {
  const { formatMessage } = useIntl();

  const {
    status,
    isLoading,
    categories,
    list: {
      items,
      selection: { count, searchText, category: selectCategory },
    },
  } = systemTemplates;
  const isListFullLoaded = useMemo(() => count === items.length, [count, items]);

  const [searchQuery, setSearchQuery] = useState(searchText);
  const [activeCategory, setActiveCategory] = useState(selectCategory);

  useEffect(() => changeTemplatesSystemSelectionCategory(activeCategory), [activeCategory]);

  useEffect(() => {
    debounceChangeTemplatesSystemSelectionSearch(searchQuery);
  }, [searchQuery]);

  const debounceChangeTemplatesSystemSelectionSearch = useCallback(
    debounce(500, changeTemplatesSystemSelectionSearch),
    [],
  );

  const skeleton = Array.from(Array(LOADERS_QUANTITY), (_, index) => <TemplateSystemSkeleton key={index} />);

  const renderSearchField = () => {
    return (
      <div className={styles['search-field']}>
        <div className={styles['search-field__icon']}>
          <SearchLargeIcon />
        </div>
        <InputField
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          className={styles['search-field__input']}
          onClear={() => setSearchQuery('')}
          placeholder={formatMessage({ id: 'templates.templates-search' })}
          fieldSize="md"
        />
      </div>
    );
  };

  const renderCategoriesItems = () => {
    return (
      <div className={styles['categories']}>
        <PerfectScrollbar
          className={styles['scrollbar-container']}
          options={{ suppressScrollY: true, wheelPropagation: false }}
        >
          {categories.map((category: ITemplatesSystemCategories) => (
            <TemplateSystemCategoryItem
              isActive={category.id === activeCategory}
              key={category.id}
              id={category.id}
              name={category.name}
              icon={category.icon}
              color={category.color}
              onActiveCategory={setActiveCategory}
            />
          ))}
        </PerfectScrollbar>
      </div>
    );
  };

  const renderTemplates = () => {
    if (status === ETemplatesSystemStatus.Searching) {
      return <div className={styles['cards-wrapper']}>{skeleton}</div>;
    }

    if (status === ETemplatesSystemStatus.NoTemplates) {
      return renderPlaceholder();
    }

    return (
      <InfiniteScroll
        dataLength={items.length}
        next={() => changeTemplatesSystemPaginationNext()}
        loader={skeleton}
        hasMore={!isListFullLoaded || isLoading}
        className={styles['cards-wrapper']}
      >
        {items.map((template: ISystemTemplate) => {
          const categoryLocal = categories.filter(
            (category: ITemplatesSystemCategories) => category.id === template.category,
          )[0];

          return (
            <TemplateSystemCard
              key={template.id}
              id={template.id}
              name={template.name}
              description={template.description}
              order={template.order}
              icon={categoryLocal?.icon}
              color={categoryLocal?.templateColor}
            />
          );
        })}
      </InfiniteScroll>
    );
  };

  const renderPlaceholder = () => {
    return (
      <Placeholder
        title={formatMessage({ id: 'templates.no-templates.title' })}
        description={formatMessage({ id: 'templates.no-templates.description' })}
        Icon={TasksPlaceholderIcon}
        mood="bad"
        containerClassName={styles['placeholder']}
      />
    );
  };

  return (
    <>
      <PageTitle titleId={EPageTitle.TemplatesSystem} className={styles['title']} withUnderline={false} />
      {renderSearchField()}
      {renderCategoriesItems()}
      {renderTemplates()}
    </>
  );
}

export interface ITemplatesSystemProps {
  systemTemplates: ITemplatesSystem;
  changeTemplatesSystemSelectionSearch(payload: string): void;
  changeTemplatesSystemSelectionCategory(payload: number | null): void;
  changeTemplatesSystemPaginationNext(payload: void): void;
}
