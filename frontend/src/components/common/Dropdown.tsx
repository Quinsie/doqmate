import type  { ReactElement } from 'react';
import { useState, cloneElement } from 'react';
import { useNavigate } from 'react-router-dom';

interface DropdownProps {
  trigger: ReactElement;
  children: React.ReactNode;
  defaultOpen?: boolean;
  isCollapsed?: boolean;
  collapsedNavigateTo?: string;
}

function Dropdown({ trigger, children, defaultOpen = false, isCollapsed = false, collapsedNavigateTo }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const navigate = useNavigate();

  const handleClick = () => {
    if (isCollapsed && collapsedNavigateTo) {
      navigate(collapsedNavigateTo);
    } else if (!isCollapsed) {
      setIsOpen(!isOpen);
    }
  };

  // trigger에 isCollapsed와 isOpen prop을 전달
  const triggerWithProps = cloneElement(trigger, {
    isCollapsed,
    isOpen
  } as any);

  return (
    <div className="mb-2">
      <div onClick={handleClick} className="cursor-pointer">
        {triggerWithProps}
      </div>
      {isOpen && !isCollapsed && <div className="ml-8 mt-1">{children}</div>}
    </div>
  );
}

export default Dropdown;
