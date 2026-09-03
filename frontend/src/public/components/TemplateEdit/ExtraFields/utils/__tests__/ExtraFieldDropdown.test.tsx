import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { ExtraFieldDropdown } from '../ExtraFieldDropdown';
import { Dropdown, TDropdownOption } from '../../../../UI';
import { enMessages } from '../../../../../lang/locales/en_US';
import { EFieldRuleType } from '../../../../../types/fieldset';

jest.mock('../../../../UI', () => {
  const actual = jest.requireActual('../../../../UI');
  return {
    ...actual,
    Dropdown: jest.fn(actual.Dropdown),
  };
});

jest.mock('react-outside-click-handler', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const baseProps = {
  isRequired: false,
  isRequiredDisabled: false,
  isHidden: false,
  onEditField: jest.fn(),
  onDeleteField: jest.fn(),
  onMoveFieldUp: jest.fn(),
  onMoveFieldDown: jest.fn(),
  showDatasetOption: false,
  datasetOptions: [],
  onDatasetSelect: jest.fn(),
};

const renderWithIntl = (ui: React.ReactElement) =>
  render(<IntlProvider locale="en" messages={enMessages}>{ui}</IntlProvider>);

describe('ExtraFieldDropdown', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const getRequiredSwitch = () => screen.getByRole('switch', { name: 'Required', hidden: true });
  const getHiddenSwitch = () => screen.getByRole('switch', { name: 'Hidden', hidden: true });

  describe('Render', () => {
    it('renders Hidden switch', () => {
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isHidden={false} />);

      expect(getHiddenSwitch()).toBeInTheDocument();
    });
  });

  describe('Required / Hidden mutual exclusion', () => {
    it('Required switch is disabled when field is hidden', () => {
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isHidden={true} />);

      expect(getRequiredSwitch()).toBeDisabled();
    });

    it('Hidden switch is disabled when field is required', () => {
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isRequired={true} />);

      expect(getHiddenSwitch()).toBeDisabled();
    });

    it('Required switch is disabled when isRequiredDisabled', () => {
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isRequiredDisabled={true} />);

      expect(getRequiredSwitch()).toBeDisabled();
    });
  });

  describe('Callbacks', () => {
    it('toggling Hidden on calls onEditField with isHidden=true', () => {
      const onEditField = jest.fn();
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isHidden={false} onEditField={onEditField} />);

      userEvent.click(getHiddenSwitch());

      expect(onEditField).toHaveBeenCalledTimes(1);
      expect(onEditField).toHaveBeenCalledWith({ isHidden: true });
    });

    it('toggling Hidden off calls onEditField with isHidden=false', () => {
      const onEditField = jest.fn();
      renderWithIntl(<ExtraFieldDropdown {...baseProps} isHidden={true} onEditField={onEditField} />);

      userEvent.click(getHiddenSwitch());

      expect(onEditField).toHaveBeenCalledTimes(1);
      expect(onEditField).toHaveBeenCalledWith({ isHidden: false });
    });
  });

  describe('Dataset option for list field types', () => {
    const onDatasetSelect = jest.fn();
    const datasetProps = {
      ...baseProps,
      showDatasetOption: true,
      datasetOptions: [
        { label: 'Dataset A', value: '1' },
        { label: 'Dataset B', value: '2' },
      ],
      onDatasetSelect,
    };

    it('calls onDatasetSelect with dataset id when dataset option is clicked', () => {
      renderWithIntl(<ExtraFieldDropdown {...datasetProps} />);

      userEvent.click(screen.getByText('Dataset A'));

      expect(onDatasetSelect).toHaveBeenCalledWith(1);
    });
    it('renders dataset sub-options when datasetOptions is provided', () => {
      renderWithIntl(<ExtraFieldDropdown {...datasetProps} />);

      expect(screen.getByText('Dataset A')).toBeInTheDocument();
      expect(screen.getByText('Dataset B')).toBeInTheDocument();
    });

    it('passes dataset subOptions to Dropdown when datasetOptions is provided', () => {
      (Dropdown as jest.Mock).mockClear();

      renderWithIntl(<ExtraFieldDropdown {...datasetProps} />);

      const dropdownProps = (Dropdown as jest.Mock).mock.calls[0]?.[0];
      const datasetMenuItem = dropdownProps.options.find(
        (option: TDropdownOption) => option.className && option.className.includes('dataset-submenu'),
      );
      expect(datasetMenuItem.subOptions).toBeDefined();
      expect(datasetMenuItem.subOptions.length).toBeGreaterThan(0);
    });
  });

  describe('Rulesets submenu for fields with rulesets', () => {
    const onOpenFieldRules = jest.fn();
    const rulesetProps = {
      ...baseProps,
      onOpenFieldRules,
      fieldRulesets: [
        { apiName: 'rule_1', name: 'Rule 1', type: EFieldRuleType.Validator, message: null, order: 1, groupsOr: [] },
      ],
    };

    it('renders Rulesets submenu with side-submenu styling class', () => {
      (Dropdown as jest.Mock).mockClear();
      renderWithIntl(<ExtraFieldDropdown {...rulesetProps} />);

      const dropdownProps = (Dropdown as jest.Mock).mock.calls[0]?.[0];
      const rulesetMenuItem = dropdownProps.options.find(
        (option: TDropdownOption) =>
          option.className &&
          option.className.includes('dataset-submenu') &&
          option.className.includes('dropdown-item-rules'),
      );
      expect(rulesetMenuItem).toBeDefined();
      expect(rulesetMenuItem.subOptions).toHaveLength(2);
    });

    it('triggers onOpenFieldRules with undefined when Add new ruleset is clicked', () => {
      renderWithIntl(<ExtraFieldDropdown {...rulesetProps} />);

      userEvent.click(screen.getByText('Add new ruleset'));

      expect(onOpenFieldRules).toHaveBeenCalledWith();
    });

    it('triggers onOpenFieldRules with ruleset object when an existing ruleset is clicked', () => {
      renderWithIntl(<ExtraFieldDropdown {...rulesetProps} />);

      userEvent.click(screen.getByText('Rule 1'));

      expect(onOpenFieldRules).toHaveBeenCalledWith(rulesetProps.fieldRulesets[0]);
    });

    it('triggers onDeleteFieldRuleset with ruleset apiName when deletion is confirmed', () => {
      const onDeleteFieldRuleset = jest.fn();
      renderWithIntl(<ExtraFieldDropdown {...rulesetProps} onDeleteFieldRuleset={onDeleteFieldRuleset} />);

      const dropdownProps = (Dropdown as jest.Mock).mock.calls[0]?.[0];
      const rulesetMenuItem = dropdownProps.options.find(
        (option: TDropdownOption) =>
          option.className &&
          option.className.includes('dataset-submenu') &&
          option.className.includes('dropdown-item-rules'),
      );
      const ruleOption = rulesetMenuItem.subOptions[1];
      const renderedLabel = ruleOption.label(jest.fn());

      const { container: labelContainer } = renderWithIntl(renderedLabel);
      const deleteIcon = labelContainer.querySelector('.delete-icon');
      if (deleteIcon) {
        userEvent.click(deleteIcon);
        userEvent.click(screen.getByRole('button', { name: 'Yes', hidden: true }));
        expect(onDeleteFieldRuleset).toHaveBeenCalledWith('rule_1');
      }
    });
  });
});
