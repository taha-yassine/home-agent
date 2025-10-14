import React from "react";
import { Highlight, themes } from "prism-react-renderer";
const themeLight = themes.vsLight;
const themeDark = themes.vsDark;
import { useTheme } from "../hooks/useTheme";

interface JsonCodeBlockProps {
  value: unknown;
}

const JsonCodeBlock: React.FC<JsonCodeBlockProps> = ({ value }) => {
  const { resolvedTheme } = useTheme();
  const code =
    typeof value === "string" ? value : JSON.stringify(value, null, 2);

  return (
    <Highlight
      theme={resolvedTheme === "dark" ? (themeDark as any) : (themeLight as any)}
      code={code}
      language="json"
    >
      {({ className, style, tokens, getLineProps, getTokenProps }) => (
        <pre
          className={`${className} text-xs whitespace-pre-wrap overflow-x-auto rounded-md p-3 bg-transparent border border-zinc-200 dark:border-zinc-800`}
          style={style as React.CSSProperties}
        >
          {tokens.map((line, i) => (
            <div key={i} {...getLineProps({ line })}>
              {line.map((token, key) => (
                <span key={key} {...getTokenProps({ token })} />
              ))}
            </div>
          ))}
        </pre>
      )}
    </Highlight>
  );
};

export default JsonCodeBlock;


