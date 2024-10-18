import * as React from 'react';
import * as PerfectScrollbar from 'react-perfect-scrollbar';
import { useIntl } from 'react-intl';

import { Loader, SectionTitle } from '../UI';
import { ITemplateListItem } from '../../types/template';
import { SearchIcon } from '../icons';
import { SideModal } from '../UI/SideModal';
import { useDelayUnmount } from '../../hooks/useDelayUnmount';

import { StartProcessModalItem } from './SelectTemplateModalItem';
import { openRunWorkflowModalSideMenu } from '../../redux/actions';

import styles from './SelectTemplateModal.css';

const ScrollBar = PerfectScrollbar as unknown as Function;

export interface ISelectTemplateModalProps {
  isAdmin: boolean;
  isLoading: boolean;
  ancestorTaskId: number | null;
  items: ITemplateListItem[];
  isModalOpened: boolean;
  loadSelectTemplateModalTemplates(): void;
  setSelectTemplateModalTemplates(payload: ITemplateListItem[]): void;
  openRunWorkflowModal: typeof openRunWorkflowModalSideMenu;
  closeSelectTemplateModal(): void;
}

export function SelectTemplateModal({
  isLoading,
  items,
  ancestorTaskId,
  isModalOpened,
  closeSelectTemplateModal,
  loadSelectTemplateModalTemplates,
  setSelectTemplateModalTemplates,
  openRunWorkflowModal,
}: ISelectTemplateModalProps) {
  const { useEffect, useState } = React;
  const intl = useIntl();

  const [searchText, setSearchText] = useState('');
  const [filteredTemplates, setFilteredTemplates] = useState<ITemplateListItem[]>([]);

  useEffect(() => {
    const newFilteredTemplates = items.filter(({ name }) => name.toLowerCase().includes(searchText.toLowerCase()));
    setFilteredTemplates(newFilteredTemplates);
  }, [items, searchText]);

  const handleCloseModal = () => {
    closeSelectTemplateModal();
  };

  const renderItemsList = () => {
    return (
      <ScrollBar
        options={{ suppressScrollX: true, wheelPropagation: false }}
        className={styles['body__scrollbar-container']}
      >
        <div className={styles['body__items-list']}>
          {filteredTemplates.map((template) => {
            return (
              <StartProcessModalItem
                {...template}
                selectWorkflow={() =>
                  openRunWorkflowModal({ templateData: template, ...(ancestorTaskId && { ancestorTaskId }) })
                }
                key={template.id}
              />
            );
          })}
        </div>
      </ScrollBar>
    );
  };

  const shouldRender = useDelayUnmount(isModalOpened, 150);
  if (!shouldRender) {
    return null;
  }

  return (
    <SideModal
      onOpen={loadSelectTemplateModalTemplates}
      onClose={handleCloseModal}
      onAfterClose={() => setSelectTemplateModalTemplates([])}
      isClosing={!isModalOpened}
    >
      <SideModal.Header className={styles['start-process-modal__header']}>
        <div className={styles['header__input-container']}>
          <SearchIcon className={styles['header__search-icon']} />
          <input
            value={searchText}
            className={styles['header__input']}
            placeholder={intl.formatMessage({ id: 'select-template.input-placeholder' })}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </div>
      </SideModal.Header>
      <SideModal.Body className={styles['modal__body']}>
        <Loader isLoading={isLoading} />

        <SectionTitle className={styles['title']}>{intl.formatMessage({ id: 'select-template.title' })}</SectionTitle>

        {renderItemsList()}
      </SideModal.Body>
    </SideModal>
  );
}
