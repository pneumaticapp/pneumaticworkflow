import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';

import { TemplateFieldContext } from '../../../useTemplateForm/contexts';
import { ITemplateClient } from '../../../../../types/template';
import { KickoffShareForm } from '../KickoffShareForm';

jest.mock('react-intl', () => ({
  useIntl: () => ({ formatMessage: ({ id }: { id: string }) => id }),
}));

jest.mock('react-redux', () => ({
  useSelector: jest.fn(),
}));

jest.mock('rc-switch', () => ({
  __esModule: true,
  default: (props: { checked: boolean }) => (
    <input type="checkbox" aria-label="share switch" checked={props.checked} readOnly />
  ),
}));

jest.mock('../../../useTemplateForm', () => {
  const { useTemplateField } = jest.requireActual('../../../useTemplateForm/contexts');

  return { useTemplateField };
});

jest.mock('../../../../UI', () => ({
  Tabs: (props: {
    values: { id: string; label: string }[];
    activeValueId: string;
    onChange: (id: string) => void;
  }) => (
    <div data-testid="tabs" data-active={props.activeValueId}>
      {props.values.map((tab) => (
        <button type="button" key={tab.id} onClick={() => props.onChange(tab.id)}>
          {tab.label}
        </button>
      ))}
    </div>
  ),
}));

jest.mock('../KickoffShareTabs', () => ({
  SharedFormTab: (props: {
    isSuccessUrlEnabled: boolean;
    successUrl: string;
    onToggleSuccessUrl: () => void;
  }) => (
    <div
      data-testid="shared-tab"
      data-success-enabled={String(props.isSuccessUrlEnabled)}
      data-success-url={props.successUrl}
    >
      <button type="button" onClick={props.onToggleSuccessUrl}>Toggle redirect</button>
    </div>
  ),
  EmbeddedFormTab: () => <div data-testid="embedded-tab" />,
}));

const makeTemplate = (overrides: Partial<ITemplateClient> = {}) => ({
  id: 1,
  publicUrl: null,
  isPublic: false,
  publicSuccessUrl: null,
  embedUrl: null,
  isEmbedded: false,
  ...overrides,
}) as ITemplateClient;

function renderShareForm(values: ITemplateClient) {
  const setFieldValue = jest.fn();

  const view = render(
    <TemplateFieldContext.Provider value={{ values, setFieldValue, setValues: jest.fn() }}>
      <KickoffShareForm />
    </TemplateFieldContext.Provider>,
  );

  return {
    ...view,
    rerenderWithValues: (nextValues: ITemplateClient) => view.rerender(
      <TemplateFieldContext.Provider value={{ values: nextValues, setFieldValue, setValues: jest.fn() }}>
        <KickoffShareForm />
      </TemplateFieldContext.Provider>,
    ),
  };
}

function StatefulShareForm({ initialValues }: { initialValues: ITemplateClient }) {
  const [values, setValues] = React.useState(initialValues);

  return (
    <TemplateFieldContext.Provider
      value={{
        values,
        setFieldValue: jest.fn(),
        setValues: (nextValues) => setValues(nextValues),
      }}
    >
      <KickoffShareForm />
      <output data-testid="form-values">{JSON.stringify(values)}</output>
    </TemplateFieldContext.Provider>
  );
}

describe('KickoffShareForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockReturnValue(true);
  });

  it('syncs share and redirect UI from updated form values', () => {
    const { rerenderWithValues } = renderShareForm(makeTemplate());

    expect(screen.queryByTestId('shared-tab')).not.toBeInTheDocument();

    rerenderWithValues(makeTemplate({
      isPublic: true,
      publicUrl: 'https://forms.test/form',
      publicSuccessUrl: 'https://forms.test/success',
    }));

    expect(screen.getByTestId('shared-tab')).toHaveAttribute('data-success-enabled', 'true');
    expect(screen.getByTestId('shared-tab')).toHaveAttribute('data-success-url', 'https://forms.test/success');
  });

  it('treats externally loaded empty redirect URL as disabled', () => {
    renderShareForm(makeTemplate({
      isPublic: true,
      publicUrl: 'https://forms.test/form',
      publicSuccessUrl: '',
    }));

    expect(screen.getByTestId('shared-tab')).toHaveAttribute('data-success-enabled', 'false');
    expect(screen.getByTestId('shared-tab')).toHaveAttribute('data-success-url', '');
  });

  it('keeps entered redirect URL while the toggle is temporarily disabled', () => {
    render(
      <StatefulShareForm
        initialValues={makeTemplate({
          isPublic: true,
          publicUrl: 'https://forms.test/form',
          publicSuccessUrl: 'https://forms.test/success',
        })}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Toggle redirect' }));

    expect(screen.getByTestId('shared-tab')).toHaveAttribute('data-success-enabled', 'false');
    expect(screen.getByTestId('shared-tab')).toHaveAttribute('data-success-url', 'https://forms.test/success');

    userEvent.click(screen.getByRole('button', { name: 'Toggle redirect' }));

    expect(screen.getByTestId('shared-tab')).toHaveAttribute('data-success-enabled', 'true');
    expect(screen.getByTestId('shared-tab')).toHaveAttribute('data-success-url', 'https://forms.test/success');
  });

  it('updates public and embedded sharing fields in one form transaction', () => {
    render(<StatefulShareForm initialValues={makeTemplate()} />);

    userEvent.click(screen.getByRole('button', { name: /kickoff\.share-control/ }));

    expect(JSON.parse(screen.getByTestId('form-values').textContent || '')).toEqual(
      expect.objectContaining({
        isPublic: true,
        publicUrl: '',
        isEmbedded: true,
        embedUrl: '',
      }),
    );
  });

  it('syncs active tab when form values switch to embedded-only sharing', () => {
    const { rerenderWithValues } = renderShareForm(makeTemplate({
      isPublic: true,
      publicUrl: 'https://forms.test/form',
    }));

    expect(screen.getByTestId('shared-tab')).toBeInTheDocument();

    rerenderWithValues(makeTemplate({
      isEmbedded: true,
      embedUrl: 'https://forms.test/embed',
    }));

    expect(screen.getByTestId('tabs')).toHaveAttribute('data-active', 'embedded');
    expect(screen.getByTestId('embedded-tab')).toBeInTheDocument();
  });
});
