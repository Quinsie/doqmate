interface ChatbotTagSelectorProps {
  options: readonly string[];
  selectedTag: string;
  customTag: string;
  onTagChange: (tag: string) => void;
  onCustomTagChange: (customTag: string) => void;
}

// const TAG_OPTIONS = ['선택 없음', '소비자', '농가', '직원'] as const;

function ChatbotTagSelector({
  options,
  selectedTag,
  customTag,
  onTagChange,
  onCustomTagChange
}: ChatbotTagSelectorProps) {
  const handleTagSelect = (tag: string) => {
    onTagChange(tag);
    if (tag !== 'custom') {
      onCustomTagChange('');
    }
  };

  const handleCustomTagInput = (value: string) => {
    onCustomTagChange(value);
    onTagChange('custom');
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
      <h2 className="text-lg font-bold mb-6 text-left">
        챗봇 태그
      </h2>

      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="flex gap-3 items-center">
            {options.map((tag) => (
              <label key={tag} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="chatbotTag"
                  value={tag}
                  checked={selectedTag === tag}
                  onChange={(e) => handleTagSelect(e.target.value)}
                  className="w-4 h-4"
                />
                <span className="text-gray-700">{tag}</span>
              </label>
            ))}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="chatbotTag"
                value="custom"
                checked={selectedTag === 'custom'}
                onChange={(e) => onTagChange(e.target.value)}
                className="w-4 h-4"
              />
              <span className="text-gray-700">직접 입력</span>
            </label>
            <input
              type="text"
              value={customTag}
              onChange={(e) => handleCustomTagInput(e.target.value)}
              onFocus={() => onTagChange('custom')}
              placeholder="태그 입력"
              className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-40"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatbotTagSelector;
