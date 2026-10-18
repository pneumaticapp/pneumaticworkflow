import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { Formik } from 'formik';

import { FormikDropdownList } from '../DropdownList';

const renderWithError = (error: string) =>
  render(
    <Formik
      initialValues={{ vendor: '' }}
      initialErrors={{ vendor: error }}
      initialTouched={{ vendor: true }}
      onSubmit={jest.fn()}
    >
      <FormikDropdownList name="vendor" label="Vendor" options={[{ label: 'OpenAI', value: 'openai' }]} />
    </Formik>,
  );

describe('FormikDropdownList', () => {
  it('translates an error that is a message id', () => {
    renderWithError('validation.field-required');

    expect(screen.getByText('This field is required')).toBeInTheDocument();
    expect(screen.queryByText('validation.field-required')).not.toBeInTheDocument();
  });

  it('shows an already translated error as is', () => {
    renderWithError('Select a vendor');

    expect(screen.getByText('Select a vendor')).toBeInTheDocument();
  });
});
