/* prettier-ignore */
import { connect } from 'react-redux';
import { SelectMenu, ISelectMenuProps } from '../../components/UI';
import { ETemplatesSorting } from '../../types/workflow';
import type { RootState } from '../../redux/store';
import { changeTemplatesSorting } from '../../redux/actions';
import { workflowsSortingValues } from '../../constants/sortings';

type TMapStateToProps = Pick<ISelectMenuProps<ETemplatesSorting>, 'activeValue' | 'values'>;
type TMapDispatchToProps = Pick<ISelectMenuProps<ETemplatesSorting>, 'onChange'>;

const mapStateToProps = ({ templates: { templatesListSorting } }: RootState): TMapStateToProps => {
  return {
    activeValue: templatesListSorting,
    values: workflowsSortingValues,
  };
};

const mapDispatchToProps: TMapDispatchToProps = {
  onChange: changeTemplatesSorting,
};

export const TemplatesSortingContainer = connect<TMapStateToProps, TMapDispatchToProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SelectMenu);
