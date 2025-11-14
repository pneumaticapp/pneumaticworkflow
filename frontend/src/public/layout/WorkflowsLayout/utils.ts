import { getUserFullName } from '../../utils/users';

export enum ERenderPlaceholderType {
  Template = 'template',
  Starter = 'starter',
}

interface IGetRenderPlaceholder {
  filterIds: number[];
  options: any[];
  formatMessage: (id: { id: string }, values?: { count: number }) => string;
  type: ERenderPlaceholderType;
  severalOptionPlaceholder: string;
  defaultPlaceholder: string;
}

export const getRenderPlaceholder = ({
  filterIds,
  options,
  formatMessage,
  type,
  severalOptionPlaceholder,
  defaultPlaceholder,
}: IGetRenderPlaceholder) => {
  if (filterIds.length === 1) {
    const selectedOPtion = options.find((option) => option.id === filterIds[0]);
    if (type === ERenderPlaceholderType.Template) {
      return selectedOPtion?.name || '';
    } if (type === ERenderPlaceholderType.Starter) {
      return getUserFullName(selectedOPtion);
    }
  } else if (filterIds.length > 1) {
    return formatMessage({ id: severalOptionPlaceholder }, { count: filterIds.length });
  }
  return formatMessage({ id: defaultPlaceholder });
};
