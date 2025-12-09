interface PageHeaderProps {
  title: string;
  description?: string;
}

function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-4">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">{title}</h1>
      {description && <p className="text-gray-600">{description}</p>}
    </div>
  );
}

export default PageHeader;
