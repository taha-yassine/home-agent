import { Sun, Moon, Monitor, SunMoon } from "lucide-react";
import { useTheme } from "../hooks/useTheme";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  const getIcon = () => {
    switch (theme) {
      case "light":
        return <Sun className="w-5 h-5" />;
      case "dark":
        return <Moon className="w-5 h-5" />;
      case "system":
        return <SunMoon className="w-5 h-5" />;
    }
  };

  const getTitle = () => {
    switch (theme) {
      case "light":
        return "Switch to dark mode";
      case "dark":
        return "Switch to system default";
      case "system":
        return "Switch to light mode";
    }
  };

  return (
    <button
      onClick={toggleTheme}
      title={getTitle()}
      className="p-2 rounded-md text-zinc-500 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition-colors cursor-pointer"
    >
      {getIcon()}
    </button>
  );
} 