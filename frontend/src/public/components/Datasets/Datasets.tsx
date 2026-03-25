import * as React from 'react';
import { PageTitle } from '../PageTitle';
import { EPageTitle } from '../../constants/defaultValues';

export function Datasets() {
  return (
    <div>
      <PageTitle titleId={EPageTitle.Datasets} withUnderline={false} />
    </div>
  );
}

export default Datasets;
