import React, { ReactNode, useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { userEvent, within } from '@storybook/test';

import { ETaskListSorting } from '../../../types/tasks';
import { EUserStatus, TUserListItem } from '../../../types/user';
import { DropdownList } from '../DropdownList';
import { TDropdownOptionBase } from '../DropdownList/types';
import { UsersDropdownComponent } from '../form/UsersDropdown/UsersDropdown';
import { EOptionTypes, TUsersDropdownOption } from '../form/UsersDropdown/types';
import { FilterSelect } from './FilterSelect';
import { SelectMenu } from './SelectMenu';

type TOption = { label: string; value: string };
type TTemplate = { id: number; name: string };

const noOp = () => undefined;

/** Every story reserves room below the control so an opened menu never needs scrolling. */
const ROOM = 460;

const OPTIONS: TOption[] = [
  { label: 'Workflow starter', value: 'starter' },
  { label: 'Specific user', value: 'user' },
  { label: 'User group', value: 'group' },
  { label: 'Field value', value: 'field' },
];

const TEMPLATES: TTemplate[] = [
  { id: 1, name: 'Customer onboarding' },
  { id: 2, name: 'Invoice approval' },
  { id: 3, name: 'Content review' },
];

const USERS = [
  {
    id: 1,
    email: 'maya.chen@example.com',
    firstName: 'Maya',
    lastName: 'Chen',
    phone: '',
    photo: '',
    type: 'user',
    status: EUserStatus.Active,
  },
  {
    id: 2,
    email: 'david.okafor@example.com',
    firstName: 'David',
    lastName: 'Okafor',
    phone: '',
    photo: '',
    type: 'user',
    status: EUserStatus.Active,
  },
] as TUserListItem[];

const USER_OPTIONS: TUsersDropdownOption[] = USERS.map((user) => ({
  id: user.id,
  label: `${user.firstName} ${user.lastName}`,
  value: `${EOptionTypes.User}-${user.id}`,
  optionType: EOptionTypes.User,
}));

function Case({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', alignItems: 'stretch' }}>
      <span style={{ fontSize: '1.1rem', letterSpacing: '0.06em', textTransform: 'uppercase', opacity: 0.48 }}>
        {title}
      </span>
      {children}
    </div>
  );
}

/** A fixed grid keeps every case in its own column, so the gallery reads as a table. */
function Gallery({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(28rem, 1fr))',
        gap: '3.2rem',
        alignItems: 'start',
      }}
    >
      {children}
    </div>
  );
}

const openFirstMenu = async ({ canvasElement }: { canvasElement: HTMLElement }) => {
  const [toggle] = within(canvasElement).getAllByRole('button');
  await userEvent.click(toggle);
};

const meta = {
  title: 'UI/Dropdowns/Select',
  component: DropdownList,
  tags: ['autodocs'],
  decorators: [
    // `room` reserves vertical space for the open menu, `storyWidth` keeps single controls narrow.
    (Story, { parameters }) => (
      <div style={{ minHeight: parameters.room || ROOM, padding: '1.6rem', maxWidth: parameters.storyWidth || 420 }}>
        <Story />
      </div>
    ),
  ],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Value selection: forms, filters and user pickers. `DropdownList` is the base (built on '
          + '`react-select`); `FilterSelect`, `SelectMenu` and `UsersDropdown` are presets over the same '
          + 'menu surface. Use `Dropdown` for action menus such as edit/delete instead.',
      },
    },
  },
  argTypes: {
    controlSize: { control: 'inline-radio', options: ['lg', 'sm'] },
    placement: { control: 'inline-radio', options: [undefined, 'left', 'right'] },
    isSearchable: { control: 'boolean' },
    isMulti: { control: 'boolean' },
    isDisabled: { control: 'boolean' },
    isRequired: { control: 'boolean' },
    staticMenu: { control: 'boolean' },
    label: { control: 'text' },
    placeholder: { control: 'text' },
    errorMessage: { control: 'text' },
  },
  args: {
    options: OPTIONS,
    placeholder: 'Select a value',
    controlSize: 'lg',
    isSearchable: false,
    isMulti: false,
    isDisabled: false,
    isRequired: false,
    staticMenu: false,
  },
} satisfies Meta<typeof DropdownList<TOption>>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Tweak every prop from the controls panel. Uncontrolled: the component keeps the selection. */
export const Playground: Story = {};

/** Both control sizes, closed and opened. */
export const Sizes: Story = {
  parameters: { room: 380, storyWidth: '100%' },
  render: (args) => (
    <Gallery>
      <Case title="lg — the form control">
        <DropdownList<TOption> {...args} controlSize="lg" />
      </Case>
      <Case title="sm — the compact chip">
        <DropdownList<TOption> {...args} controlSize="sm" title="Sort by" />
      </Case>
    </Gallery>
  ),
};

/** Label, required marker and the error state a form shows on validation. */
export const LabelAndError: Story = {
  parameters: { room: 320, storyWidth: '100%' },
  render: (args) => (
    <Gallery>
      <Case title="With label">
        <DropdownList<TOption> {...args} label="Condition field" />
      </Case>
      <Case title="Required">
        <DropdownList<TOption> {...args} label="Condition field" isRequired />
      </Case>
      <Case title="Error">
        <DropdownList<TOption> {...args} label="Condition field" errorMessage="This field is required" />
      </Case>
      <Case title="Disabled">
        <DropdownList<TOption> {...args} label="Condition field" isDisabled />
      </Case>
    </Gallery>
  ),
};

/** The search field lives inside the menu at both sizes. */
export const Searchable: Story = {
  play: openFirstMenu,
  args: { isSearchable: true, placeholder: 'Search values' },
};

/** Multi select keeps the menu open and marks every chosen option. */
export const Multiple: Story = {
  play: openFirstMenu,
  args: { isMulti: true, isSearchable: true, placeholder: 'Search values' },
};

/** Options can arrive grouped under headings. */
export const Grouped: Story = {
  play: openFirstMenu,
  args: {
    options: [
      { label: 'System events', options: [{ label: 'Workflow started', value: 'started' }] },
      { label: 'Date fields', options: [{ label: 'Due date', value: 'due' }, { label: 'Start date', value: 'start' }] },
    ],
  },
};

/** No toggle at all — the menu is always open and renders in the page flow. */
export const StaticMenu: Story = {
  args: { staticMenu: true, isSearchable: true },
};

/** Empty state when a search matches nothing. */
export const NoOptions: Story = {
  play: openFirstMenu,
  args: { options: [], isSearchable: true, noOptionsMessage: 'Nothing found' },
};

function ControlledStory() {
  const [value, setValue] = useState<TOption | null>(OPTIONS[0]);

  return (
    <DropdownList<TOption>
      label="Controlled value"
      options={OPTIONS}
      value={value}
      onChange={(option: TDropdownOptionBase) => setValue(option as TOption)}
    />
  );
}

/** Controlled: the consumer owns the selection. */
export const Controlled: Story = { render: () => <ControlledStory /> };

function FilterSelectMultipleStory() {
  const [selected, setSelected] = useState<(number | string)[]>([]);

  return (
    <FilterSelect<'id', 'name', TTemplate>
      isMultiple
      isSearchShown
      options={TEMPLATES}
      optionIdKey="id"
      optionLabelKey="name"
      selectAllLabel="Select all"
      noValueLabel="All templates"
      placeholderText="No templates"
      searchPlaceholder="Search templates"
      selectedOptions={selected}
      resetFilter={() => setSelected([])}
      onChange={(next: (number | string)[]) => setSelected(next)}
      renderPlaceholder={() => (selected.length ? `${selected.length} selected` : 'All templates')}
    />
  );
}

const filterSelectBaseProps = {
  options: TEMPLATES,
  optionIdKey: 'id' as const,
  optionLabelKey: 'name' as const,
  noValueLabel: 'All templates',
  placeholderText: 'No templates',
  selectedOption: null,
  resetFilter: noOp,
  onChange: noOp,
  renderPlaceholder: () => 'All templates',
};

/** `FilterSelect` — the list filters above workflows and tasks. */
export const FilterSelectVariants: Story = {
  name: 'Preset: FilterSelect',
  parameters: { room: 520, storyWidth: '100%' },
  render: () => (
    <Gallery>
      <Case title="Default">
        <FilterSelect<'id', 'name', TTemplate> {...filterSelectBaseProps} />
      </Case>
      <Case title="With search">
        <FilterSelect<'id', 'name', TTemplate> {...filterSelectBaseProps} isSearchShown searchPlaceholder="Search" />
      </Case>
      <Case title="Wide menu">
        <FilterSelect<'id', 'name', TTemplate> {...filterSelectBaseProps} isSearchShown isWideMenu />
      </Case>
      <Case title="Loading">
        <FilterSelect<'id', 'name', TTemplate> {...filterSelectBaseProps} isLoading />
      </Case>
      <Case title="Disabled">
        <FilterSelect<'id', 'name', TTemplate> {...filterSelectBaseProps} isDisabled />
      </Case>
      <Case title="Multiple + select all">
        <FilterSelectMultipleStory />
      </Case>
    </Gallery>
  ),
};

function SelectMenuInteractiveStory({ withRadio }: { withRadio?: boolean }) {
  const [sorting, setSorting] = useState(ETaskListSorting.DateDesc);

  return (
    <SelectMenu<ETaskListSorting>
      closeOnSelect
      withRadio={withRadio}
      values={Object.values(ETaskListSorting)}
      activeValue={sorting}
      onChange={setSorting}
    />
  );
}

/** `SelectMenu` — the sorting picker. */
export const SelectMenuVariants: Story = {
  name: 'Preset: SelectMenu',
  parameters: { room: 420, storyWidth: '100%' },
  render: () => (
    <Gallery>
      <Case title="Default">
        <SelectMenuInteractiveStory />
      </Case>
      <Case title="With radio">
        <SelectMenuInteractiveStory withRadio />
      </Case>
      <Case title="Hide selected option">
        <SelectMenu<ETaskListSorting>
          hideSelectedOption
          closeOnSelect
          values={Object.values(ETaskListSorting)}
          activeValue={ETaskListSorting.DateDesc}
          onChange={noOp}
        />
      </Case>
      <Case title="Disabled">
        <SelectMenu<ETaskListSorting>
          isDisabled
          values={Object.values(ETaskListSorting)}
          activeValue={ETaskListSorting.DateDesc}
          onChange={noOp}
        />
      </Case>
    </Gallery>
  ),
};

function UsersDropdownStory({ controlSize, title }: { controlSize: 'lg' | 'sm'; title?: string }) {
  const [selected, setSelected] = useState<TUsersDropdownOption[]>([]);
  const toggle = (option: TUsersDropdownOption) => setSelected((current) => (
    current.some(({ id }) => id === option.id)
      ? current.filter(({ id }) => id !== option.id)
      : [...current, option]
  ));

  return (
    <UsersDropdownComponent
      isMulti
      isAdmin
      controlSize={controlSize}
      title={title}
      options={USER_OPTIONS}
      users={USERS}
      value={selected}
      placeholder="Search"
      inviteLabel="Invite team member"
      isTeamInvitesModalOpen={false}
      recentInvitedUsers={[]}
      onChange={toggle}
      onChangeSelected={toggle}
      onClickInvite={noOp}
      openTeamInvitesPopup={noOp}
      onClickAllUsers={(selectAll: boolean) => setSelected(selectAll ? USER_OPTIONS : [])}
    />
  );
}

/** `UsersDropdown` — avatars, checkboxes and the invite / all-users entries. */
export const UsersDropdownVariants: Story = {
  name: 'Preset: UsersDropdown',
  parameters: { room: 560, storyWidth: '100%' },
  render: () => (
    <Gallery>
      <Case title="Single">
        <UsersDropdownComponent
          isAdmin
          options={USER_OPTIONS}
          users={USERS}
          placeholder="Search"
          inviteLabel="Invite team member"
          isTeamInvitesModalOpen={false}
          recentInvitedUsers={[]}
          onChange={noOp}
          onClickInvite={noOp}
          openTeamInvitesPopup={noOp}
        />
      </Case>
      <Case title="Multiple">
        <UsersDropdownStory controlSize="lg" />
      </Case>
      <Case title="Add performer (sm)">
        <UsersDropdownStory controlSize="sm" title="Add performer" />
      </Case>
      <Case title="With label and error">
        <UsersDropdownComponent
          isAdmin
          isRequired
          label="Substitutes"
          errorMessage="Please select at least one substitute"
          options={USER_OPTIONS}
          users={USERS}
          placeholder="Search"
          inviteLabel="Invite team member"
          isTeamInvitesModalOpen={false}
          recentInvitedUsers={[]}
          onChange={noOp}
          onClickInvite={noOp}
          openTeamInvitesPopup={noOp}
        />
      </Case>
    </Gallery>
  ),
};
