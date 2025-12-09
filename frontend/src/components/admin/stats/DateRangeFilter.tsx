export type DateRange = 'all' | '7' | '30' | '90';

interface DateRangeFilterProps {
  value: DateRange;
  onChange: (value: DateRange) => void;
}

const OPTIONS: { value: DateRange; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: '7', label: '최근 7일' },
  { value: '30', label: '최근 30일' },
  { value: '90', label: '최근 90일' },
];

function DateRangeFilter({ value, onChange }: DateRangeFilterProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as DateRange)}
      className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      {OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

export default DateRangeFilter;
