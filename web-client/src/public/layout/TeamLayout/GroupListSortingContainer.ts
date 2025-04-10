import { connect } from 'react-redux';
import { SelectMenu, ISelectMenuProps } from '../../components/UI';
import { IApplicationState } from '../../types/redux';
import { EGroupsListSorting } from '../../types/user';
import { groupListSortingValues } from '../../constants/sortings';
import { changeGroupsListSorting } from '../../redux/actions';

type TMapStateToProps = Pick<ISelectMenuProps<EGroupsListSorting>, 'activeValue' | 'values'>;
type TMapDispatchToProps = Pick<ISelectMenuProps<EGroupsListSorting>, 'onChange'>;

const mapStateToProps = ({ groups: { groupsListSorting }}: IApplicationState): TMapStateToProps => {
  return {
    activeValue: groupsListSorting,
    values: groupListSortingValues,
  };
};

const mapDispatchToProps: TMapDispatchToProps  = {
  onChange: changeGroupsListSorting,
};

export const GroupListSortingContainer = connect<TMapStateToProps, TMapDispatchToProps>
(mapStateToProps, mapDispatchToProps)(SelectMenu);
