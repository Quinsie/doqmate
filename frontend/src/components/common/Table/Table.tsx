import type { TableProps } from './types';

function Table<T>({
  data,
  columns,
  keyExtractor,
  onRowClick,
  selectedKey,
  isLoading = false,
  emptyMessage = '데이터가 없습니다.',
  fixedLayout = false,
}: TableProps<T>) {
  const getAlignClass = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'left':
        return 'text-left';
      case 'right':
        return 'text-right';
      default:
        return 'text-center';
    }
  };

  const getCellValue = (row: T, key: string): unknown => {
    return (row as Record<string, unknown>)[key];
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-gray-500">
        로딩 중...
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-gray-500">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className={`w-full text-sm ${fixedLayout ? 'table-fixed' : ''}`}>
        <thead>
          <tr className="bg-blue-50">
            {columns.map((column, colIndex) => (
              <th
                key={column.key}
                className={`
                  py-4 px-5 font-semibold text-gray-600
                  ${getAlignClass(column.align)}
                  ${column.width || ''}
                  ${colIndex === 0 ? 'rounded-l-lg' : ''}
                  ${colIndex === columns.length - 1 ? 'rounded-r-lg' : ''}
                `}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => {
            const rowKey = keyExtractor(row);
            const isSelected = selectedKey === rowKey;
            const isLast = rowIndex === data.length - 1;
            const isClickable = !!onRowClick || selectedKey !== undefined;

            return (
              <tr
                key={rowKey}
                onClick={() => onRowClick?.(row, rowIndex)}
                className={`
                  transition-all
                  ${isClickable ? 'cursor-pointer' : ''}
                  ${isSelected
                    ? 'bg-blue-50 border-l-4 border-l-blue-500'
                    : `${isClickable ? 'hover:bg-gray-50' : ''} border-l-4 border-l-transparent`
                  }
                  ${!isLast ? 'border-b border-gray-100' : ''}
                `}
              >
                {columns.map((column) => {
                  const value = getCellValue(row, column.key);
                  const content = column.render
                    ? column.render(value, row, rowIndex)
                    : (value as React.ReactNode);

                  return (
                    <td
                      key={column.key}
                      className={`py-4 px-5 ${getAlignClass(column.align)} ${column.width || ''}`}
                    >
                      {content}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default Table;
