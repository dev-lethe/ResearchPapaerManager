import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#F8F9FA",
        surface: "#FFFFFF",
        textPrimary: "#1F2937",
        textSecondary: "#6B7280",
        border: "#E5E7EB",
        accent: "#3B5BDB",
        hover: "#EEF2FF",
        danger: "#DC2626",
        success: "#15803D",
      },
      borderRadius: {
        card: "6px",
        modal: "8px",
      },
    },
  },
  plugins: [],
};

export default config;
