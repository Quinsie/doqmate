export interface TableColumn<T> {
  key: string;
  label: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, row: T, index: number) => React.ReactNode;
}

export interface TableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  keyExtractor: (row: T) => string;
  onRowClick?: (row: T, index: number) => void;
  selectedKey?: string | null;
  isLoading?: boolean;
  emptyMessage?: string;
  fixedLayout?: boolean;
}
