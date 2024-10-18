import React, { useEffect } from 'react';
import { TITLES } from '../../constants/titles';
import { ITemplatesList, ITemplatesSystem } from '../../types/redux';
import { ETemplatesSorting } from '../../types/workflow';
import { TCloneTemplatePayload, TDeleteTemplatePayload } from '../../redux/actions';
import { TemplatesUser } from './TemplatesUser';
import { TemplatesSystem } from './TemplatesSystem';

import styles from './Templates.css';

export interface ITemplatesProps {
  templatesList: ITemplatesList;
  loading?: boolean;
  canEdit: boolean | undefined;
  templatesListSorting: ETemplatesSorting;
  systemTemplates: ITemplatesSystem;
  loadTemplatesSystemCategories(payload: void): void;
  cloneTemplate(payload: TCloneTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
  loadTemplates(offset: number): void;
  changeTemplatesSystemSelectionSearch(payload: string): void;
  changeTemplatesSystemSelectionCategory(payload: number | null): void;
  changeTemplatesSystemPaginationNext(payload: void): void;
  loadTemplatesSystem(payload: void): void;
  resetTemplates(): void;
  openRunWorkflowModal(payload: { templateId: number }): void;
  setIsAITemplateModalOpened(value: boolean): void;
}

export function Templates({
  templatesList,
  loading,
  canEdit,
  systemTemplates,
  loadTemplatesSystemCategories,
  cloneTemplate,
  deleteTemplate,
  loadTemplates,
  loadTemplatesSystem,
  resetTemplates,
  changeTemplatesSystemSelectionSearch,
  changeTemplatesSystemSelectionCategory,
  changeTemplatesSystemPaginationNext,
  openRunWorkflowModal,
  setIsAITemplateModalOpened,
}: ITemplatesProps) {
  useEffect(() => {
    document.title = TITLES.Templates;
    loadTemplates(0);
    loadTemplatesSystem();
    loadTemplatesSystemCategories();
    return () => resetTemplates();
  }, []);

  return (
    <div className={styles['container']}>
      <TemplatesUser
        loading={loading}
        templatesList={templatesList}
        canEdit={canEdit}
        cloneTemplate={cloneTemplate}
        deleteTemplate={deleteTemplate}
        loadTemplates={loadTemplates}
        openRunWorkflowModal={openRunWorkflowModal}
        setIsAITemplateModalOpened={setIsAITemplateModalOpened}
      />
      <TemplatesSystem
        systemTemplates={systemTemplates}
        changeTemplatesSystemSelectionSearch={changeTemplatesSystemSelectionSearch}
        changeTemplatesSystemSelectionCategory={changeTemplatesSystemSelectionCategory}
        changeTemplatesSystemPaginationNext={changeTemplatesSystemPaginationNext}
      />
    </div>
  );
}
