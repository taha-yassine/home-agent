import React from "react";

interface SchemaViewerProps {
  schema: any; // A valid JSON Schema object of type "object"
}

function getType(prop: any): string {
  if (prop.type) {
    return Array.isArray(prop.type) ? prop.type.join(" | ") : prop.type;
  }
  if (prop.anyOf) {
    return prop.anyOf.map((p: { type?: string }) => p.type || "unknown").join(" | ");
  }
  if (prop.oneOf) {
    return prop.oneOf.map((p: { type?: string }) => p.type || "unknown").join(" | ");
  }
  return "unknown";
}

const SchemaViewer: React.FC<SchemaViewerProps> = ({ schema }) => {
  if (
    !schema ||
    schema.type !== "object" ||
    !schema.properties ||
    Object.keys(schema.properties).length === 0
  ) {
    return (
      <div className="text-sm text-zinc-500 dark:text-zinc-400">
        No parameters required.
      </div>
    );
  }

  const requiredFields = new Set(schema.required || []);

  return (
    <div className="divide-y divide-zinc-200 dark:divide-zinc-800 -m-2">
      {Object.entries(schema.properties).map(([name, prop]: [string, any]) => (
        <div key={name} className="py-3 px-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <code className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                {name}
              </code>
              {requiredFields.has(name) && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                  Required
                </span>
              )}
            </div>
            <code className="text-xs text-zinc-500 dark:text-zinc-400">
              {getType(prop)}
            </code>
          </div>

          {prop.description && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
              {prop.description}
            </p>
          )}
        </div>
      ))}
    </div>
  );
};

export default SchemaViewer; 