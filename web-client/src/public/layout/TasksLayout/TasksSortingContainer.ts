/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { SelectMenu, ISelectMenuProps } from '../../components/UI';
import { IApplicationState } from '../../types/redux';
import { changeTasksSorting } from '../../redux/actions';
import { processesTasksCompleteSortingValues, processesTasksSortingValues } from '../../constants/sortings';
import { ETaskListCompleteSorting, ETaskListCompletionStatus, ETaskListSorting } from '../../types/tasks';

type TMapStateToProps = Pick<ISelectMenuProps<ETaskListSorting | ETaskListCompleteSorting>, 'activeValue' | 'values'>;
type TMapDispatchToProps = Pick<ISelectMenuProps<ETaskListSorting | ETaskListCompleteSorting>, 'onChange'>;

const mapStateToProps = ({
  tasks: { tasksSettings: { sorting, completionStatus } },
}: IApplicationState): TMapStateToProps => {
  return {
    activeValue: sorting,
    values: completionStatus === ETaskListCompletionStatus.Completed ?
      processesTasksCompleteSortingValues :
      processesTasksSortingValues,
  };
};

const mapDispatchToProps: TMapDispatchToProps = {
  onChange: changeTasksSorting,
};

export const TasksSortingContainer = connect<TMapStateToProps, TMapDispatchToProps>
(mapStateToProps, mapDispatchToProps)(SelectMenu);
