import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';
import { ITemplatesProps, Templates } from './Templates';
import {
  loadTemplatesSystem,
  loadTemplates,
  resetTemplates,
  changeTemplatesSorting,
  openRunWorkflowModalByTemplateId,
  cloneTemplate,
  deleteTemplate,
  setIsAITemplateModalOpened,
  loadTemplatesSystemCategories,
  changeTemplatesSystemSelectionSearch,
  changeTemplatesSystemSelectionCategory,
  changeTemplatesSystemPaginationNext,
} from '../../redux/actions';
import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { ETemplatesSorting } from '../../types/workflow';

type TStoreProps = Pick<
  ITemplatesProps,
  'templatesList' | 'loading' | 'canEdit' | 'templatesListSorting' | 'systemTemplates'
>;

type TDispatchProps = Pick<
  ITemplatesProps,
  | 'loadTemplatesSystem'
  | 'loadTemplatesSystemCategories'
  | 'loadTemplates'
  | 'openRunWorkflowModal'
  | 'resetTemplates'
  | 'cloneTemplate'
  | 'deleteTemplate'
  | 'changeTemplatesSystemSelectionSearch'
  | 'changeTemplatesSystemSelectionCategory'
  | 'changeTemplatesSystemPaginationNext'
  | 'setIsAITemplateModalOpened'
>;

export function mapStateToProps({
  authUser: { isAccountOwner, isAdmin },
  templates: { isListLoading, templatesList, templatesListSorting, systemTemplates },
}: IApplicationState): TStoreProps {
  const canEdit = isAccountOwner || isAdmin;

  return {
    systemTemplates,
    canEdit,
    loading: isListLoading,
    templatesList,
    templatesListSorting,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  loadTemplatesSystemCategories,
  loadTemplatesSystem,
  loadTemplates,
  openRunWorkflowModal: openRunWorkflowModalByTemplateId,
  resetTemplates,
  cloneTemplate,
  deleteTemplate,
  setIsAITemplateModalOpened,
  changeTemplatesSystemSelectionSearch,
  changeTemplatesSystemSelectionCategory,
  changeTemplatesSystemPaginationNext,
};

const SyncedTemplates = withSyncedQueryString<TStoreProps>([
  {
    propName: 'templatesListSorting',
    queryParamName: 'sorting',
    defaultAction: changeTemplatesSorting(ETemplatesSorting.DateDesc),
    createAction: changeTemplatesSorting,
    getQueryParamByProp: (value) => value,
  },
])(Templates);

export const TemplatesContainer = connect<TStoreProps, TDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SyncedTemplates);
