interface SubMenuItemProps {
  label: string;
  onClick?: () => void;
}

function SubMenuItem({ label, onClick }: SubMenuItemProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left px-4 py-2 text-sm text-gray-600 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-all duration-200 whitespace-nowrap overflow-hidden"
    >
      {label}
    </button>
  );
}

export default SubMenuItem;
