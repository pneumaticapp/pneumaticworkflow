import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import type { FormatOptionLabelMeta } from 'react-select';

import { ETaskListSorting } from '../../../types/tasks';
import { EUserStatus, TUserListItem } from '../../../types/user';
import { ConditionDropdownOption } from '../../TemplateEdit/TaskForm/Conditions/ConditionDropdownOption';
import { DropdownButton } from '../Buttons/DropdownButton';
import { DropdownArea } from '../DropdownArea';
import { DropdownList } from '../DropdownList';
import { EModifyDropdownToggle, ModifyDropdown } from '../ModifyDropdown';
import { FilterSelect, SelectMenu } from '../Select';
import { EOptionTypes, TUsersDropdownOption, UsersDropdownComponent } from '../form/UsersDropdown';
import { Dropdown } from './Dropdown';

import styles from './Dropdown.stories.css';

const noOp = () => undefined;
const meta = {
  title: 'UI/Dropdowns',
  parameters: { layout: 'centered' },
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const ActionMenus: Story = {
  render: () => (
    <div className={styles['canvas']}>
      <Dropdown
        renderToggle={() => 'Actions'}
        options={[
          { label: 'Edit', onClick: noOp },
          { label: 'Duplicate', onClick: noOp },
          { label: 'Delete', color: 'red', withUpperline: true, withConfirmation: true, onClick: noOp },
        ]}
      />
      <ModifyDropdown
        editLabel="Edit"
        deleteLabel="Delete"
        cloneLabel="Clone"
        onEdit={noOp}
        onDelete={noOp}
        onClone={noOp}
        toggleType={EModifyDropdownToggle.Modify}
      />
    </div>
  ),
};

const formOptions = [
  { label: 'Workflow starter', value: 'starter' },
  { label: 'Specific user', value: 'user' },
  { label: 'User group', value: 'group' },
];
type TFormOption = typeof formOptions[number];
const formatConditionOption = (option: TFormOption, formatMeta: FormatOptionLabelMeta<TFormOption>) => (
  <ConditionDropdownOption
    label={option.label}
    isSelected={formatMeta.selectValue.some(({ value }) => value === option.value)}
  />
);
const users: TUserListItem[] = [
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
];
const userOptions: TUsersDropdownOption[] = users.map((user) => ({
  id: user.id,
  label: `${user.firstName} ${user.lastName}`,
  value: String(user.id),
  optionType: EOptionTypes.User,
}));

function FormSelectionsStory() {
  const [value, setValue] = useState(formOptions[0]);
  const [selectedUsers, setSelectedUsers] = useState<TUsersDropdownOption[]>([]);
  const toggleUser = (option: TUsersDropdownOption) => setSelectedUsers((current) => (
    current.some(({ id }) => id === option.id)
      ? current.filter(({ id }) => id !== option.id)
      : [...current, option]
  ));

  return (
    <div className={styles['canvas']}>
      <div className={styles['column']}>
        <DropdownList<TFormOption>
          label="Condition value"
          options={formOptions}
          value={value}
          onChange={(option) => setValue(option)}
          formatOptionLabel={formatConditionOption}
        />
      </div>
      <UsersDropdownComponent
        controlSize="sm"
        title="Add performer"
        isMulti
        options={userOptions}
        users={users}
        value={selectedUsers}
        inviteLabel="Invite team member"
        isTeamInvitesModalOpen={false}
        recentInvitedUsers={[]}
        isAdmin
        onChange={toggleUser}
        onClickInvite={noOp}
        openTeamInvitesPopup={noOp}
        onClickAllUsers={(selectAll) => setSelectedUsers(selectAll ? userOptions : [])}
      />
    </div>
  );
}

export const FormSelections: Story = { render: () => <FormSelectionsStory /> };

function FiltersStory() {
  const [templateId, setTemplateId] = useState<number | string | null>(null);
  const [sorting, setSorting] = useState(ETaskListSorting.DateDesc);
  const templates = [{ id: 1, name: 'Customer onboarding' }, { id: 2, name: 'Invoice approval' }];

  return (
    <div className={styles['canvas']}>
      <FilterSelect
        options={templates}
        optionIdKey="id"
        optionLabelKey="name"
        placeholderText="No templates"
        noValueLabel="All templates"
        selectedOption={templateId}
        resetFilter={() => setTemplateId(null)}
        onChange={setTemplateId}
        renderPlaceholder={() => templates.find(({ id }) => id === templateId)?.name || 'All templates'}
      />
      <SelectMenu<ETaskListSorting>
        values={Object.values(ETaskListSorting)}
        activeValue={sorting}
        onChange={setSorting}
        closeOnSelect
      />
    </div>
  );
}

export const Filters: Story = { render: () => <FiltersStory /> };

export const CustomContentAndButton: Story = {
  render: () => (
    <div className={styles['canvas']}>
      <DropdownArea title="Add guest">
        <p className={styles['content']}>Any contextual content can use the same menu positioning and dismissal behavior.</p>
      </DropdownArea>
      <DropdownButton
        dropdownOptions={[
          { itemHeaderIntlId: 'general.modify', onClick: noOp },
          { itemHeaderIntlId: 'dropdown.yes', itemDescriptionIntlId: 'dropdown.are-you-sure', onClick: noOp },
        ]}
      />
    </div>
  ),
};
