import React from 'react';
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

jest.mock('../../../../UI/OutsideClickHandler', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('reactstrap/lib/DropdownMenu', () => {
  const ReactLocal = require('react');
  const { DropdownContext } = require('reactstrap/lib/DropdownContext');
  return {
    __esModule: true,
    default: ({ children }: { children: React.ReactNode }) => {
      const context = ReactLocal.useContext(DropdownContext);
      return ReactLocal.createElement('div', { role: 'menu', 'aria-hidden': !context.isOpen }, children);
    },
  };
});

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
  render(
    <IntlProvider locale="en" messages={enMessages}>
      {ui}
    </IntlProvider>,
  );

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

    describe('Interactive deletion and dropdown closing in Rulesets submenu', () => {
      const RULESETS_LABEL = enMessages['fieldsets.field-rulesets-submenu'];
      const DELETE_RULE_LABEL = enMessages['fieldsets.rule-delete'];
      const YES_LABEL = enMessages['dropdown.yes'];
      const NO_LABEL = enMessages['dropdown.no'];

      const openRulesetsSubmenu = () => {
        const toggleButton = screen.getByRole('button');
        userEvent.click(toggleButton);
        userEvent.click(screen.getByRole('button', { name: RULESETS_LABEL }));
        return toggleButton;
      };

      it('enters deletion confirmation mode without React validateDOMNesting warning', () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => undefined);

        try {
          renderWithIntl(<ExtraFieldDropdown {...rulesetProps} onDeleteFieldRuleset={jest.fn()} />);
          openRulesetsSubmenu();

          userEvent.click(screen.getByRole('button', { name: DELETE_RULE_LABEL }));

          expect(screen.getByRole('button', { name: YES_LABEL })).toBeInTheDocument();
          expect(screen.getByRole('button', { name: NO_LABEL })).toBeInTheDocument();
          const hasDomNestingWarning = consoleErrorSpy.mock.calls.some((callArgs) =>
            callArgs.some((argument) => typeof argument === 'string' && argument.includes('validateDOMNesting')),
          );
          expect(hasDomNestingWarning).toBe(false);
        } finally {
          consoleErrorSpy.mockRestore();
        }
      });

      it('closes dropdown when an existing ruleset name is clicked', () => {
        renderWithIntl(<ExtraFieldDropdown {...rulesetProps} />);
        const toggleButton = openRulesetsSubmenu();

        expect(toggleButton).toHaveAttribute('aria-expanded', 'true');

        userEvent.click(screen.getByRole('button', { name: 'Rule 1' }));

        expect(onOpenFieldRules).toHaveBeenCalledTimes(1);
        expect(onOpenFieldRules).toHaveBeenCalledWith(rulesetProps.fieldRulesets[0]);
        expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
      });

      it('calls onDeleteFieldRuleset and closes dropdown when deletion is confirmed', () => {
        const onDeleteFieldRuleset = jest.fn();
        renderWithIntl(<ExtraFieldDropdown {...rulesetProps} onDeleteFieldRuleset={onDeleteFieldRuleset} />);
        const toggleButton = openRulesetsSubmenu();

        userEvent.click(screen.getByRole('button', { name: DELETE_RULE_LABEL }));
        userEvent.click(screen.getByRole('button', { name: YES_LABEL }));

        expect(onDeleteFieldRuleset).toHaveBeenCalledTimes(1);
        expect(onDeleteFieldRuleset).toHaveBeenCalledWith('rule_1');
        expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
      });

      it('keeps dropdown open and skips deletion when No is clicked', () => {
        const onDeleteFieldRuleset = jest.fn();
        renderWithIntl(<ExtraFieldDropdown {...rulesetProps} onDeleteFieldRuleset={onDeleteFieldRuleset} />);
        const toggleButton = openRulesetsSubmenu();

        userEvent.click(screen.getByRole('button', { name: DELETE_RULE_LABEL }));
        userEvent.click(screen.getByRole('button', { name: NO_LABEL }));

        expect(onDeleteFieldRuleset).not.toHaveBeenCalled();
        expect(screen.getByRole('button', { name: 'Rule 1' })).toBeInTheDocument();
        expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
      });
    });
  });
});
