import { getUserFullName } from '../../utils/users';

export enum ERenderPlaceholderType {
  Template = 'template',
  Starter = 'starter',
  Performer = 'performer',
}

interface IGetRenderPlaceholder {
  isDisabled?: boolean;
  filterType?: 'userType' | 'groupType';
  filterIds: number[];
  options: any[];
  formatMessage: (id: { id: string }, values?: { count: number }) => string;
  type: ERenderPlaceholderType;
  severalOptionPlaceholder: string;
  defaultPlaceholder: string;
}

export const getRenderPlaceholder = ({
  isDisabled,
  filterType,
  filterIds,
  options,
  formatMessage,
  type,
  severalOptionPlaceholder,
  defaultPlaceholder,
}: IGetRenderPlaceholder) => {
  if (filterIds.length === 0 || isDisabled) {
    return formatMessage({ id: defaultPlaceholder });
  } if (filterIds.length > 1) {
    return formatMessage({ id: severalOptionPlaceholder }, { count: filterIds.length });
  } 
  const selectedOption = options.find((option) => option.id === filterIds[0]);

  if (
    type === ERenderPlaceholderType.Template ||
      (type === ERenderPlaceholderType.Performer && filterType === 'groupType')
  ) {
    return selectedOption?.name || '';
  }

  if (
    type === ERenderPlaceholderType.Starter ||
      (type === ERenderPlaceholderType.Performer && filterType === 'userType')
  ) {
    return getUserFullName(selectedOption);
  }
  return formatMessage({ id: defaultPlaceholder });
  
};
