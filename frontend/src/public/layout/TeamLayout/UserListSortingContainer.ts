import { connect } from 'react-redux';
import { SelectMenu, ISelectMenuProps } from '../../components/UI';
import type { RootState } from '../../redux/store';
import { EUserListSorting } from '../../types/user';
import { userListSortingChanged as changeUserListSorting } from '../../redux/accounts/slice';
import { userListSortingValues } from '../../constants/sortings';

type TMapStateToProps = Pick<ISelectMenuProps<EUserListSorting>, 'activeValue' | 'values'>;
type TMapDispatchToProps = Pick<ISelectMenuProps<EUserListSorting>, 'onChange'>;

const mapStateToProps = ({ accounts: { userListSorting } }: RootState): TMapStateToProps => {
  return {
    activeValue: userListSorting,
    values: userListSortingValues,
  };
};

const mapDispatchToProps: TMapDispatchToProps = {
  onChange: changeUserListSorting,
};

export const UserListSortingContainer = connect<TMapStateToProps, TMapDispatchToProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SelectMenu);
