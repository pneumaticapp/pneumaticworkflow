/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

import { Filter, TOptionBase } from '../Filter';

const options = [{ id: 0, name: 'Jane' }, { id: 1, name: 'Mary' }, { id: 2, name: 'Alex' }];
const changeFilter = jest.fn();

describe('Filter', () => {
  it('Renders expanded list if isInitiallyExpanded prop is passed', () => {
    render(
      <Filter
        title="Filter's title"
        options={options}
        optionIdKey="id"
        optionLabelKey="name"
        changeFilter={changeFilter}
        selectedOption={0}
        isInitiallyExpanded
      />,
    );

    expect(screen.getByRole('list')).toBeInTheDocument();
    expect(screen.getByText(/Jane/)).toBeInTheDocument();
  });
  it('Renders not expanded list if isInitiallyExpanded prop is passed', () => {
    render(
      <Filter
        title="Filter's title"
        options={options}
        optionIdKey="id"
        optionLabelKey="name"
        changeFilter={changeFilter}
        selectedOption={null}
      />,
    );

    expect(screen.queryByRole('list')).toBeNull();
  });
  it('Renders list with checkboxes if isMultiple', () => {
    render(
      <Filter
        isMultiple
        title="Filter's title"
        options={options}
        optionIdKey="id"
        optionLabelKey="name"
        changeFilter={changeFilter}
        selectedOptions={[]}
        isInitiallyExpanded
      />,
    );

    const checkbox = document.querySelector('[type="checkbox"]');
    expect(checkbox).toBeInTheDocument();
  });
  it('Search works correctly', () => {
    render(
      <Filter
        isMultiple
        withSearch
        title="Filter's title"
        options={options}
        optionIdKey="id"
        optionLabelKey="name"
        changeFilter={changeFilter}
        selectedOptions={[]}
        isInitiallyExpanded
      />,
    );

    const searchInput = screen.getByTestId('search-input');
    expect(searchInput).toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: 'Jane' } });

    expect(screen.getByText(/Jane/)).toBeInTheDocument();
    expect(screen.queryByText(/Mary/)).toBeNull();
  });

  it('Renders suboptions', () => {
    const options: TOptionBase<'id', 'name'>[] = [
      {
        id: 0,
        name: 'Jane',
        subOptions: [
          {
            id: 0,
            name: 'Suboption 1',
          },
          {
            id: 1,
            name: 'Suboption 2',
          }
        ],
      },
      { id: 1, name: 'Mary' },
      { id: 2, name: 'Alex' }
    ];

    render(
      <Filter
        isMultiple
        title="Filter's title"
        options={options}
        optionIdKey="id"
        optionLabelKey="name"
        changeFilter={changeFilter}
        selectedOptions={[0]}
        selectedSubOptions={[]}
        isInitiallyExpanded
      />,
    );

    const showSubOptionsBtn = screen.getByTestId('show-sub-options');
    fireEvent.click(showSubOptionsBtn);

    expect(screen.getByText(/Suboption 1/)).toBeInTheDocument();
  });
});
