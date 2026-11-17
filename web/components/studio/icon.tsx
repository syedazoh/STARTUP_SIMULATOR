export default function Icon({
  name,
  size = 20,
}: {
  name: string;
  size?: number;
}) {
  const paths: Record<string, string> = {
    studio: "M4 7l8-4 8 4-8 4-8-4zm0 5l8 4 8-4M4 17l8 4 8-4",
    arrow: "M5 12h14m-5-5l5 5-5 5",
    back: "M19 12H5m5-5l-5 5 5 5",
    grid: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",
    cube: "M12 3l9 5v8l-9 5-9-5V8l9-5zm0 9v9M3 8l9 4 9-4",
    check: "M5 12l4 4L19 6",
    clock: "M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
    play: "M8 5l11 7-11 7V5z",
    pause: "M8 5v14M16 5v14",
    refresh:
      "M20 7v5h-5M4 17v-5h5M5 8a8 8 0 0 1 13-3l2 3M4 16l2 3a8 8 0 0 0 13-3",
    chevron: "M9 5l7 7-7 7",
    list: "M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01",
    expand: "M8 3H3v5M16 3h5v5M21 16v5h-5M8 21H3v-5",
    cross: "M6 6l12 12M18 6L6 18",
    signal: "M5 19v-4M10 19V11M15 19V7M20 19V3",
    logout: "M9 4H4v16h5M12 12h9m-4-4l4 4-4 4",
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] || paths.cube} />
    </svg>
  );
}
