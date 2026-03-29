"use client";

import { FC } from "react";
import { useTheme } from "next-themes";
import clsx from "clsx";

import { SunFilledIcon, MoonFilledIcon } from "@/components/icons";

export interface ThemeSwitchProps {
  className?: string;
}

export const ThemeSwitch: FC<ThemeSwitchProps> = ({ className }) => {
  const { theme, setTheme } = useTheme();
  const isLight = theme === "light";

  const onChange = () => {
    isLight ? setTheme("dark") : setTheme("light");
  };

  return (
    <button
      type="button"
      onClick={onChange}
      aria-label={`Switch to ${isLight ? "dark" : "light"} mode`}
      className={clsx(
        "px-px transition-opacity hover:opacity-80 cursor-pointer",
        className,
      )}
    >
      <div className="w-auto h-auto bg-transparent rounded-lg flex items-center justify-center text-default-500 pt-px px-0 mx-0">
        {isLight ? <SunFilledIcon size={22} /> : <MoonFilledIcon size={22} />}
      </div>
    </button>
  );
};
