import * as React from 'react';
import { useDispatch } from 'react-redux';

import { TopNavContainer } from '../../components/TopNav';
import { WorkflowModalContainer } from '../../components/Workflows/WorkflowModal';
import { closeWorkflowLogPopup, loadHighlights } from '../../redux/actions';

interface IHighlightsLayoutProps {
  children: React.ReactNode;
}

export function HighlightsLayout({ children }: IHighlightsLayoutProps) {
  const dispatch = useDispatch();

  return (
    <>
      <TopNavContainer />
      <main>
        <div className="container-fluid">{children}</div>

        <WorkflowModalContainer
          onWorkflowEnded={() => {
            dispatch(closeWorkflowLogPopup());
            dispatch(loadHighlights({}));
          }}
        />
      </main>
    </>
  );
}
