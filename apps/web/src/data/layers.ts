// Research-output layers (O1, O2, O4). Rasters are exported from the Figma map component.
export type LayerKey =
  | "vertical"
  | "eastwest"
  | "seasonal"
  | "changes"
  | "background"
  | "uncertainty";

export type Legend =
  | { kind: "ramp"; title: string; stops: string[]; ticks: string[] }
  | { kind: "classes"; title: string; items: { color: string; label: string }[] };

export type Layer = {
  key: LayerKey;
  name: string;
  code: string;
  desc: string;
  src: string;
  legend: Legend;
};

export const VERTICAL_STOPS = [
  "#f4eedf 0%",
  "#f1d9a4 11%",
  "#ebb46e 25%",
  "#de8248 43%",
  "#c34c30 61%",
  "#93292a 79%",
  "#4f1722 100%",
];

export const LAYERS: Layer[] = [
  {
    key: "vertical",
    name: "Vertical velocity",
    code: "O1",
    desc: "mm/yr, sinking positive. 100 m pixels.",
    src: "/map/vertical.png",
    legend: {
      kind: "ramp",
      title: "Vertical velocity · mm/yr, sinking +",
      stops: VERTICAL_STOPS,
      ticks: ["0", "35", "60", "85", "110", "140+"],
    },
  },
  {
    key: "eastwest",
    name: "East–west velocity",
    code: "O1",
    desc: "mm/yr. Ground moves inward around a bowl.",
    src: "/map/eastwest.png",
    legend: {
      kind: "ramp",
      title: "East–west velocity · mm/yr, east +",
      stops: ["#2f6c95 0%", "#a9c6d8 30%", "#f3f1ec 50%", "#e4b39c 70%", "#a4452a 100%"],
      ticks: ["−20", "−10", "0", "+10", "+20"],
    },
  },
  {
    key: "seasonal",
    name: "Seasonal amplitude",
    code: "O2",
    desc: "mm. Elastic, recoverable yearly motion.",
    src: "/map/seasonal.png",
    legend: {
      kind: "ramp",
      title: "Seasonal amplitude · mm",
      stops: ["#e3eaea 0%", "#a9c8cc 50%", "#5f97a1 100%"],
      ticks: ["0", "5", "10", "15+"],
    },
  },
  {
    key: "changes",
    name: "Change dates",
    code: "O2",
    desc: "When sinking sped up or slowed down.",
    src: "/map/changes.png",
    legend: {
      kind: "classes",
      title: "Change dates · year of the main change",
      items: [
        { color: "#8f2d56", label: "2016" },
        { color: "#3e1f47", label: "2017" },
        { color: "#5e8c62", label: "2018" },
        { color: "#e0a558", label: "2019" },
        { color: "#3d5a80", label: "2020" },
        { color: "#98b06e", label: "2021" },
        { color: "#c8553d", label: "2022" },
      ],
    },
  },
  {
    key: "background",
    name: "Background subsidence",
    code: "O4",
    desc: "Sinking expected without deep pumping.",
    src: "/map/background.png",
    legend: {
      kind: "ramp",
      title: "Background subsidence · mm/yr",
      stops: ["#faf7f2 0%", "#f2dcae 40%", "#e9a868 75%", "#de8248 100%"],
      ticks: ["0", "15", "30", "45+"],
    },
  },
  {
    key: "uncertainty",
    name: "Uncertainty",
    code: "O1",
    desc: "± mm/yr per pixel, from resampling.",
    src: "/map/uncertainty.png",
    legend: {
      kind: "ramp",
      title: "Uncertainty · ± mm/yr",
      stops: ["#e7e4ef 0%", "#c4bdda 50%", "#9a8fbf 100%"],
      ticks: ["0", "3", "6", "9+"],
    },
  },
];

export const layerByKey = (k: LayerKey) => LAYERS.find((l) => l.key === k)!;
