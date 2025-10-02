import * as React from 'react';

import { TemplatesSortingContainer } from './TemplatesSortingContainer';
import { TopNavContainer } from '../../components/TopNav';

import styles from './TemplatesLayout.css';

export interface ITemplatesLayoutProps {
  children: JSX.Element;
}

export function TemplatesLayout({children} : ITemplatesLayoutProps) {
  const renderWorkflowListContent = () => {
    return (
      <div className={styles['navbar-left__content']}>
        <TemplatesSortingContainer />
      </div>
    );
  };

  return (
    <>
      <TopNavContainer
        leftContent={renderWorkflowListContent()}
      />
      <main>
        <div className="container-fluid">
          {children}
        </div>
      </main>
    </>
  );
}
