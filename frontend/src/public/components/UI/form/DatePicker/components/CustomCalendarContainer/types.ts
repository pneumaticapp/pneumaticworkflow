export interface CustomCalendarContainerProps {
  onChange: (date: Date | null) => void;
  selected: Date | null;
  children: React.ReactNode;
  value: Date | null;
}