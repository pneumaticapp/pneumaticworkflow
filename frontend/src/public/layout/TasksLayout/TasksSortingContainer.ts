import { connect } from 'react-redux';
import type { ISelectMenuProps } from '../../components/UI';
import { SelectMenu } from '../../components/UI';
import type { RootState } from '../../redux/store';
import { changeTaskListSorting } from '../../redux/tasks/slice';
import { processesTasksCompleteSortingValues, processesTasksSortingValues } from '../../constants/sortings';
import type { ETaskListCompleteSorting, ETaskListSorting } from '../../types/tasks';
import { ETaskListCompletionStatus } from '../../types/tasks';

type TMapStateToProps = Pick<ISelectMenuProps<ETaskListSorting | ETaskListCompleteSorting>, 'activeValue' | 'values'>;
type TMapDispatchToProps = Pick<ISelectMenuProps<ETaskListSorting | ETaskListCompleteSorting>, 'onChange'>;

const mapStateToProps = ({
  tasks: {
    tasksSettings: { sorting, completionStatus },
  },
}: RootState): TMapStateToProps => {
  return {
    activeValue: sorting,
    values:
      completionStatus === ETaskListCompletionStatus.Completed
        ? processesTasksCompleteSortingValues
        : processesTasksSortingValues,
  };
};

const mapDispatchToProps: TMapDispatchToProps = {
  onChange: changeTaskListSorting,
};

export const TasksSortingContainer = connect<TMapStateToProps, TMapDispatchToProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SelectMenu);
