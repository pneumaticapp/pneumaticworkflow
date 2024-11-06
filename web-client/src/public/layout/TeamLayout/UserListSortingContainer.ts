/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { SelectMenu, ISelectMenuProps } from '../../components/UI';
import { IApplicationState } from '../../types/redux';
import { EUserListSorting } from '../../types/user';
import { changeUserListSorting } from '../../redux/accounts/actions';
import { userListSortingValues } from '../../constants/sortings';

type TMapStateToProps = Pick<ISelectMenuProps<EUserListSorting>, 'activeValue' | 'values'>;
type TMapDispatchToProps = Pick<ISelectMenuProps<EUserListSorting>, 'onChange'>;

const mapStateToProps = ({ accounts: { userListSorting }}: IApplicationState): TMapStateToProps => {
  return {
    activeValue: userListSorting,
    values: userListSortingValues,
  };
};

const mapDispatchToProps: TMapDispatchToProps  = {
  onChange: changeUserListSorting,
};

export const UserListSortingContainer = connect<TMapStateToProps, TMapDispatchToProps>
(mapStateToProps, mapDispatchToProps)(SelectMenu);
