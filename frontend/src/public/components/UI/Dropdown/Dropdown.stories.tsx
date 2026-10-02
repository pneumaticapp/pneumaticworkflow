import React, { ReactNode } from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { userEvent, within } from '@storybook/test';

import { AlarmIcon, PencilIcon, TrashIcon, UnionIcon } from '../../icons';
import { DropdownArea } from '../DropdownArea';
import { DropdownControl } from '../DropdownControl';
import { DropdownSurface } from '../DropdownSurface';
import { DropdownOption } from '../DropdownList/DropdownOption';
import { ModifyDropdown } from '../ModifyDropdown';
import { EModifyDropdownToggle } from '../ModifyDropdown/types';
import { DropdownButton } from '../Buttons/DropdownButton';
import { Dropdown } from './Dropdown';
import { IDropdownProps, TDropdownOption } from './types';

const noOp = () => undefined;
const renderToggle: IDropdownProps['renderToggle'] = () => 'Actions';

const ROOM = 420;

function Case({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', alignItems: 'flex-start' }}>
      <span style={{ fontSize: '1.1rem', letterSpacing: '0.06em', textTransform: 'uppercase', opacity: 0.48 }}>
        {title}
      </span>
      {children}
    </div>
  );
}

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
  title: 'UI/Dropdowns/Dropdown',
  component: Dropdown,
  tags: ['autodocs'],
  decorators: [
    (Story, { parameters }) => (
      <div style={{ minHeight: parameters.room || ROOM, padding: parameters.storyPadding || '1.6rem' }}>
        <Story />
      </div>
    ),
  ],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Action menu: Popper positioning, outside-click and Escape dismissal, confirmation items and '
          + 'submenus. Every action menu in the kit composes this one — the presets and building blocks '
          + 'below are all the same component. Use `Select` for picking a value instead.',
      },
    },
  },
  argTypes: {
    direction: {
      control: 'inline-radio',
      options: [undefined, 'right'],
      description: 'Shorthand alignment; `placement` wins when both are set.',
    },
    placement: {
      control: 'select',
      options: ['bottom-start', 'bottom-end', 'top-start', 'top-end', 'right-start', 'left-start'],
    },
    isDisabled: { control: 'boolean' },
    menuPositionFixed: { control: 'boolean' },
  },
  args: {
    renderToggle,
    isDisabled: false,
    options: [
      { label: 'Edit', onClick: noOp },
      { label: 'Duplicate', onClick: noOp },
    ],
  },
} satisfies Meta<typeof Dropdown>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Playground: Story = {};

export const OptionKinds: Story = {
  play: openFirstMenu,
  args: {
    options: [
      { label: 'Edit', Icon: PencilIcon, onClick: noOp },
      { label: 'Clone', Icon: UnionIcon, onClick: noOp },
      { label: 'Snooze', Icon: AlarmIcon, subOptions: [
        { label: 'For a day', onClick: noOp },
        { label: 'For a week', onClick: noOp },
      ] },
      { label: 'Approved', color: 'green', onClick: noOp },
      { label: 'Needs attention', color: 'orange', onClick: noOp },
      { label: 'Delete', color: 'red', Icon: TrashIcon, withUpperline: true, withConfirmation: true, onClick: noOp },
    ] as TDropdownOption[],
  },
};

export const Colors: Story = {
  play: openFirstMenu,
  args: {
    options: [
      { label: 'Default (black)', color: 'black', onClick: noOp },
      { label: 'Success (green)', color: 'green', onClick: noOp },
      { label: 'Warning (orange)', color: 'orange', onClick: noOp },
      { label: 'Danger (red)', color: 'red', onClick: noOp },
    ] as TDropdownOption[],
  },
};

export const WithConfirmation: Story = {
  play: openFirstMenu,
  args: {
    options: [
      { label: 'Edit', onClick: noOp },
      { label: 'Delete', color: 'red', withUpperline: true, withConfirmation: true, onClick: noOp },
    ] as TDropdownOption[],
  },
};

export const WithSubmenu: Story = {
  play: async (context) => {
    await openFirstMenu(context);
    const submenuRow = within(context.canvasElement).getByRole('button', { name: /Move to/ });
    await userEvent.click(submenuRow);
  },
  args: {
    options: [
      {
        label: 'Move to',
        subOptions: [
          { label: 'Backlog', onClick: noOp },
          { label: 'Archive', subOptions: [{ label: 'Last quarter', onClick: noOp }] },
        ],
      },
      { label: 'Duplicate', onClick: noOp },
    ] as TDropdownOption[],
  },
};

export const CustomSubOption: Story = {
  play: openFirstMenu,
  args: {
    options: [
      {
        label: 'Snooze until',
        Icon: AlarmIcon,
        customSubOption: (
          <div style={{ padding: '1.2rem', width: '22rem' }}>
            <p>Any element can stand in for a submenu list.</p>
          </div>
        ),
      },
      { label: 'Duplicate', onClick: noOp },
    ] as TDropdownOption[],
  },
};

export const CustomContent: Story = {
  play: openFirstMenu,
  args: {
    renderToggle: (isOpen: boolean) => (isOpen ? 'Close panel' : 'Open panel'),
    children: ({ closeDropdown }: { closeDropdown(): void }) => (
      <div style={{ padding: '1.2rem', width: '24rem' }}>
        <p>Any content can live inside the menu.</p>
        <button type="button" onClick={closeDropdown}>Close</button>
      </div>
    ),
  },
};

const placementStory = (placement: IDropdownProps['placement']): Story => ({
  name: `Placement: ${placement}`,
  play: openFirstMenu,
  parameters: { room: 480, storyPadding: '16rem 1.6rem' },
  args: { placement, renderToggle: () => placement },
});

export const PlacementBottomStart = placementStory('bottom-start');
export const PlacementBottomEnd = placementStory('bottom-end');
export const PlacementTopStart = placementStory('top-start');
export const PlacementTopEnd = placementStory('top-end');
export const PlacementRightStart = placementStory('right-start');
export const PlacementLeftStart = placementStory('left-start');

export const Disabled: Story = {
  args: { isDisabled: true },
};

export const Presets: Story = {
  parameters: { room: 520 },
  render: () => (
    <Gallery>
      <Case title="ModifyDropdown — modify">
        <ModifyDropdown
          editLabel="Edit"
          cloneLabel="Clone"
          deleteLabel="Delete"
          onEdit={noOp}
          onClone={noOp}
          onDelete={noOp}
          toggleType={EModifyDropdownToggle.Modify}
        />
      </Case>
      <Case title="ModifyDropdown — more">
        <ModifyDropdown
          editLabel="Edit"
          cloneLabel="Clone"
          deleteLabel="Delete"
          onEdit={noOp}
          onClone={noOp}
          onDelete={noOp}
          toggleType={EModifyDropdownToggle.More}
        />
      </Case>
      <Case title="ModifyDropdown — no clone">
        <ModifyDropdown
          editLabel="Edit"
          deleteLabel="Delete"
          onEdit={noOp}
          onDelete={noOp}
          toggleType={EModifyDropdownToggle.Modify}
        />
      </Case>
      <Case title="DropdownButton">
        <DropdownButton
          dropdownOptions={[
            { itemHeaderIntlId: 'general.modify', onClick: noOp },
            { itemHeaderIntlId: 'dropdown.yes', itemDescriptionIntlId: 'dropdown.are-you-sure', onClick: noOp },
          ]}
        />
      </Case>
      <Case title="DropdownButton — loading">
        <DropdownButton isLoading dropdownOptions={[{ itemHeaderIntlId: 'general.modify', onClick: noOp }]} />
      </Case>
      <Case title="DropdownButton — disabled">
        <DropdownButton isDisabled dropdownOptions={[{ itemHeaderIntlId: 'general.modify', onClick: noOp }]} />
      </Case>
      <Case title="DropdownArea">
        <DropdownArea title="Add guest">
          <div style={{ width: '28rem' }}>
            <p>Invite an external user by email. They get access to this task only.</p>
          </div>
        </DropdownArea>
      </Case>
      <Case title="DropdownArea — custom toggle">
        <DropdownArea toggle={<span>Open custom panel</span>}>
          <div style={{ width: '24rem' }}>
            <p>The toggle can be any node.</p>
          </div>
        </DropdownArea>
      </Case>
    </Gallery>
  ),
};

export const BuildingBlocks: Story = {
  parameters: { room: 320 },
  render: () => (
    <Gallery>
      <Case title="DropdownSurface">
        <DropdownSurface>
          <div style={{ width: '22rem' }}>
            <div style={{ padding: '0.6rem 1.2rem' }}>First option</div>
            <div style={{ padding: '0.6rem 1.2rem' }}>Second option</div>
          </div>
        </DropdownSurface>
      </Case>
      <Case title="DropdownControl — closed">
        <DropdownControl title="Add performer" isOpen={false} />
      </Case>
      <Case title="DropdownControl — open">
        <DropdownControl title="Add performer" isOpen />
      </Case>
      <Case title="DropdownOption">
        <DropdownSurface>
          <DropdownOption label="Specific user" isSelected={false} />
          <DropdownOption label="Selected option" isSelected />
          <DropdownOption label="A very long option label that gets truncated" isSelected={false} withTooltip />
        </DropdownSurface>
      </Case>
    </Gallery>
  ),
};
