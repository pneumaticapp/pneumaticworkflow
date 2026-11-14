import { connect } from 'react-redux';
import type { ISelectMenuProps } from '../../components/UI';
import { SelectMenu } from '../../components/UI';
import type { RootState } from '../../redux/store';
import type { EGroupsListSorting } from '../../types/user';
import { groupListSortingValues } from '../../constants/sortings';
import { changeGroupsListSorting } from '../../redux/actions';

type TMapStateToProps = Pick<ISelectMenuProps<EGroupsListSorting>, 'activeValue' | 'values'>;
type TMapDispatchToProps = Pick<ISelectMenuProps<EGroupsListSorting>, 'onChange'>;

const mapStateToProps = ({ groups: { groupsListSorting } }: RootState): TMapStateToProps => {
  return {
    activeValue: groupsListSorting,
    values: groupListSortingValues,
  };
};

const mapDispatchToProps: TMapDispatchToProps = {
  onChange: changeGroupsListSorting,
};

export const GroupListSortingContainer = connect<TMapStateToProps, TMapDispatchToProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SelectMenu);
