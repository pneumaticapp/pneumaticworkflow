/// <reference types="jest" />
import React from 'react';
import { createEvent, fireEvent, render, screen } from '@testing-library/react';

import { EExtraFieldType } from '../../../../types/template';
import { KickoffLabels } from '../KickoffLabels';

describe('KickoffLabels', () => {
  const fields = [
    {
      apiName: 'field-1',
      name: 'Field 1',
      type: EExtraFieldType.String,
      order: 1,
      userId: null,
      groupId: null,
    },
  ];

  it('prevents the default Space action and toggles once', () => {
    const onToggle = jest.fn();
    render(<KickoffLabels fields={fields} onToggle={onToggle} />);
    const toggle = screen.getByRole('button', { name: 'Toggle expand' });
    const event = createEvent.keyDown(toggle, { key: ' ' });

    fireEvent(toggle, event);

    expect(event.defaultPrevented).toBe(true);
    expect(onToggle).toHaveBeenCalledTimes(1);
  });
});
