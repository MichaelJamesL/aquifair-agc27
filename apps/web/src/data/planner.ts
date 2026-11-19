// Background (non-pumping) sinking per district, screen 10 (Q3, O4). Genuk matches the Figma
// frame; the other districts follow the table in the same frame. Outlines are drawn on the
// 1200×900 map canvas.

export type District = {
  key: string;
  name: string;
  now: number; // mm/yr, median
  bg: number; // mm/yr
  bgRange: [number, number];
  drivers: [string, number][]; // Shapley values, mm/yr
  poly: [number, number][];
};

export const DISTRICTS: District[] = [
  {
    key: "genuk",
    name: "Genuk",
    now: 96,
    bg: 27,
    bgRange: [21, 33],
    drivers: [
      ["Soft-clay thickness", 11.2],
      ["Distance to coast", 6.8],
      ["Built-up volume", 4.1],
      ["Reclaimed land", 3.3],
      ["Elevation", 1.6],
    ],
    poly: [
      [627.7, 352],
      [699.7, 346],
      [747.7, 334],
      [765.6, 420],
      [727.7, 505],
      [654.7, 522],
      [611.7, 452],
    ],
  },
  {
    key: "sayung",
    name: "Sayung",
    now: 88,
    bg: 31,
    bgRange: [25, 37],
    drivers: [
      ["Soft-clay thickness", 12.4],
      ["Distance to coast", 8.9],
      ["Reclaimed land", 5.1],
      ["Built-up volume", 3.0],
      ["Elevation", 1.6],
    ],
    poly: [
      [747.7, 334],
      [805, 325],
      [862, 316],
      [878, 420],
      [852, 505],
      [727.7, 505],
      [765.6, 420],
    ],
  },
  {
    key: "semarang-utara",
    name: "Semarang Utara",
    now: 71,
    bg: 24,
    bgRange: [19, 29],
    drivers: [
      ["Soft-clay thickness", 9.0],
      ["Built-up volume", 6.3],
      ["Distance to coast", 5.2],
      ["Reclaimed land", 2.4],
      ["Elevation", 1.1],
    ],
    poly: [
      [330, 350],
      [627.7, 352],
      [611.7, 452],
      [560, 420],
      [470, 430],
      [330, 425],
    ],
  },
  {
    key: "gayamsari",
    name: "Gayamsari",
    now: 58,
    bg: 17,
    bgRange: [13, 21],
    drivers: [
      ["Soft-clay thickness", 6.1],
      ["Built-up volume", 5.2],
      ["Distance to coast", 3.0],
      ["Elevation", 1.5],
      ["Reclaimed land", 1.2],
    ],
    poly: [
      [470, 430],
      [560, 420],
      [611.7, 452],
      [654.7, 522],
      [580, 540],
      [500, 505],
    ],
  },
];

export const districtByKey = (k: string) => DISTRICTS.find((d) => d.key === k) ?? DISTRICTS[0];
