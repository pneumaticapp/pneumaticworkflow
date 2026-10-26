import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { TemplateValidationError } from '../TemplateValidationError';
import { useOpenOnValidationError } from '../useOpenOnValidationError';
import { useValidationErrorSections } from '../useValidationErrorSections';
import { clearTemplateValidationFocus } from '../../../../redux/templateValidation/slice';
import { ETaskFormParts } from '../../types';
import type { ITemplateValidationError } from '../../../../redux/templateValidation/types';

const makeError = (overrides: Partial<ITemplateValidationError> = {}): ITemplateValidationError => ({
  apiName: 'predicate-1',
  message: 'Value is required',
  target: { taskUuid: 'task-uuid', section: ETaskFormParts.CheckIf, elementApiName: 'predicate-1' },
  entitySnapshot: '{}',
  ...overrides,
});

const mockValidationErrors = (errors: ITemplateValidationError[], batchId = 1) => {
  (useSelector as jest.Mock).mockImplementation((selector) =>
    selector({
      templateValidation: { errors, batchId, focusElementApiName: errors[0]?.target.elementApiName ?? null },
    }),
  );
};

describe('TemplateValidationError', () => {
  const dispatch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    window.HTMLElement.prototype.scrollIntoView = jest.fn();
    (useDispatch as jest.Mock).mockReturnValue(dispatch);
  });

  it('shows the message and scrolls to it when the error targets one of its api names', () => {
    mockValidationErrors([makeError()]);

    render(<TemplateValidationError apiNames={['predicate-1']} />);

    expect(screen.getByRole('alert')).toHaveTextContent('Value is required');
    expect(window.HTMLElement.prototype.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' });
    expect(dispatch).toHaveBeenCalledWith(clearTemplateValidationFocus());
  });

  it('shows the message without scrolling when the error is not the first one', () => {
    mockValidationErrors([
      makeError(),
      makeError({ apiName: 'predicate-2', target: { ...makeError().target, elementApiName: 'predicate-2' } }),
    ]);

    render(<TemplateValidationError apiNames={['predicate-2']} />);

    expect(screen.getByRole('alert')).toHaveTextContent('Value is required');
    expect(window.HTMLElement.prototype.scrollIntoView).not.toHaveBeenCalled();
  });

  it('translates a message that is a dictionary key', () => {
    mockValidationErrors([makeError({ message: 'validation.condition-incomplete' })]);

    render(<TemplateValidationError apiNames={['predicate-1']} />);

    expect(screen.getByRole('alert')).toHaveTextContent('Fill in the condition');
  });

  it('shows only errors of the requested section', () => {
    const performersError = makeError({
      apiName: 'task-1',
      target: { taskUuid: 'task-uuid', section: ETaskFormParts.AssignPerformers, elementApiName: 'task-1' },
    });
    mockValidationErrors([performersError]);

    const { rerender } = render(<TemplateValidationError apiNames={['task-1']} section={null} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    rerender(<TemplateValidationError apiNames={['task-1']} section={ETaskFormParts.AssignPerformers} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Value is required');
  });

  it('renders nothing for other elements', () => {
    mockValidationErrors([makeError()]);

    render(<TemplateValidationError apiNames={['predicate-2']} />);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

describe('useOpenOnValidationError', () => {
  function Opener({ taskUuid, onOpen }: { taskUuid: string | null; onOpen: () => void }) {
    useOpenOnValidationError(taskUuid, onOpen);

    return null;
  }

  it('opens its task once per error and again for a new error', () => {
    const onOpen = jest.fn();
    mockValidationErrors([makeError()]);
    const { rerender } = render(<Opener taskUuid="task-uuid" onOpen={onOpen} />);
    rerender(<Opener taskUuid="task-uuid" onOpen={onOpen} />);

    expect(onOpen).toHaveBeenCalledTimes(1);

    mockValidationErrors([makeError()], 2);
    rerender(<Opener taskUuid="task-uuid" onOpen={onOpen} />);

    expect(onOpen).toHaveBeenCalledTimes(2);
  });

  it('ignores errors of other tasks and of the kickoff', () => {
    const onOpen = jest.fn();
    mockValidationErrors([makeError({ target: { taskUuid: null, section: null, elementApiName: 'field-1' } })]);

    render(<Opener taskUuid="task-uuid" onOpen={onOpen} />);

    expect(onOpen).not.toHaveBeenCalled();
  });
});

describe('useValidationErrorSections', () => {
  function Sections({ taskUuid }: { taskUuid: string }) {
    const { errorSections, getSectionBatchId } = useValidationErrorSections(taskUuid);

    return <>{errorSections.map((section) => `${section}:${getSectionBatchId(section)}`).join(',')}</>;
  }

  it('returns every section with an error of the task', () => {
    mockValidationErrors([
      makeError({
        target: { taskUuid: 'task-uuid', section: ETaskFormParts.AssignPerformers, elementApiName: 'task-1' },
      }),
      makeError(),
      makeError({ target: { taskUuid: 'other-task', section: ETaskFormParts.DueIn, elementApiName: 'due-date-1' } }),
      makeError({ target: { taskUuid: 'task-uuid', section: null, elementApiName: 'citem-1' } }),
    ]);

    const { container } = render(<Sections taskUuid="task-uuid" />);

    expect(container).toHaveTextContent(`${ETaskFormParts.AssignPerformers}:1,${ETaskFormParts.CheckIf}:1`);
  });
});
