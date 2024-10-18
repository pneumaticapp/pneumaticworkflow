import * as React from 'react';
import loadable from '@loadable/component';

import { Route, Switch, Redirect } from 'react-router-dom';
import { TasksLayout } from '../../layout';
import { ERoutes } from '../../constants/routes';
import { TasksContainer } from '../../components/Tasks';
import { Loader } from '../../components/UI';

const Task = loadable(
  () => import(/* webpackChunkName: "task", webpackPrefetch: true */ '../../components/TaskDetail'),
  { fallback: <Loader isLoading /> },
);

export const TasksView = () => {
  return (
    <TasksLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.TaskDetail}
            render={(props) => {
              const {
                match: {
                  params: { id },
                },
              } = props;

              return <Task key={`task-${id}`} {...props} />;
            }}
          />
          <Route path={ERoutes.Tasks} component={TasksContainer} />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TasksLayout>
  );
};
