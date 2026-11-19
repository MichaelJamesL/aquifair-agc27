# 15 App pivot for the ASEAN Geospatial Challenge: A + B + C (research, 2026-11-19)

## Why pivot
The first app idea was a map of every pumping well and its volume. Files 12-14 rule that out:
- Sinking bowls do not point at wells: registered wells sit on ground that sinks *slower* than built-up land of the same density (file 13).
- Volumes per area are validated only at 16 km with a known regional total (file 09).
- Sinking follows soft-clay thickness (~80 % of the pattern) and a regional fall in deep-aquifer pressure, not single wells (file 14).

A plain sinking-and-flood map is not new either: published InSAR maps and global sea-level tools already exist. So the app moves from "where is each well" to **who pumps, who pays, and what to do**. Every layer has to stand on a result this project validated, or be labelled as a lead.

| Module | Question it answers | User | SDG targets |
|---|---|---|---|
| **A. Groundwater accounts** | How much groundwater is used vs declared, and what is the gap worth in tax? | Bapenda, Dinas ESDM, DPRD | 6.4, 16.6, 17.1 |
| **B. Inspection leads** | Where are new large water users that likely drilled wells without a permit? | Dinas ESDM inspectors | 6.4, 6.5, 16.6 |
| **C. Pipes instead of pumps** | Where does piped surface water replace the most groundwater, and does sinking slow after it arrives? | PDAM, Bappeda, PUPR | 6.1, 11.5, 13.1 |

---

## A. Groundwater accounts (declared vs estimated, in m³ and rupiah)

### What it shows
For each kabupaten/kota:
1. **Declared** abstraction, from the provincial ESDM dataset.
2. **Estimated** use, split into a taxable non-household part and an exempt household part.
3. **The gap**, priced with the official groundwater price (NPA).

### Facts found
**Declared volumes are open data.** Dinas ESDM Jateng publishes "NPA dan Volume Pengambilan Pengusahaan Air Tanah" per kabupaten/kota:
- XLSX files for 2020, 2021, 2022 and 2023, CC-BY.
- Kota Semarang 2023: 10,069,814 m³ (read earlier, see memory/file 09 notes).
- There is also a "persentase pengambilan air tanah" dataset (use as a share of availability, 2019-2023).
- So all 35 kabupaten/kota of Central Java can be covered, not just Semarang.

**Official groundwater price (NPA), Pergub Jateng 7/2025** (in force 18 Feb 2025; annex read from the BPK copy):
- NPA = HAB × BAT. The water base price HAB is Rp 2,561 (Wilayah A), 2,795 (B) and **2,824 (C)** per m³.
- **Wilayah C** = Kota Semarang, Kab. Demak, Kab. Kudus, Kab. Pekalongan, Kota Surakarta.
- BAT = 60 % S + 40 % P:
  - S (resource component): 16 / 9 / 4 / 1, for good quality with an alternative source, good with none, poor with an alternative, poor with none.
  - P (use group): Kelompok 1 sells water. Kelompok 2-4 are high-, medium- and low-risk businesses. Kelompok 5 is social, government, BUMD water supply.
- Five volume tiers: 0-50, 51-500, 501-1,000, 1,001-2,500 and >2,500 m³. The period is not stated in the pages read.
- The Wilayah C annex prints the 40 % P column as 0.40-2.02 for every group, which looks like a typo. The BAT totals match Wilayah A, so the NPA column is used as printed.

Wilayah C, good quality, alternative source exists (table 3a), NPA in Rp/m³:

| Group | 0-50 m³ | >2,500 m³ | Tax at 20 % (top tier) |
|---|---|---|---|
| K1 water as product | 37,277 | 78,575 | 15,715 |
| K2 high-risk business | 35,018 | 67,143 | 13,429 |
| K3 medium-risk business | 32,758 | 55,701 | 11,140 |
| K4 low-risk business | 30,499 | 44,269 | 8,854 |
| K5 social / govt / BUMD | 28,240 | 32,826 | 6,565 |

**Tax rate:** 20 % of NPA in Kota Semarang (Perda 10/2023, per DDTC News). This is also the UU 1/2022 maximum (TERC brief).

**Who is exempt:** basic household use is reported as exempt (secondary source only). The UU 1/2022 article has to be checked before households are left out of the rupiah figure.

**Who pumps (Perda Kota Semarang 2024, `realdata/semarang/perda/p.txt`):**
- 96 % of registered abstraction is industrial.
- Registered volume: 13.1 (2016), 15.5 (2017), 27.7 (2018), 13.8 (2019) Mm³.
- PDAM supplied 62 % of domestic demand and distributed 51.66 Mm³ in 2022: households 41.63, niaga 4.35, **industry only 0.22**.
- So industry runs almost entirely on its own groundwater.
- PDAM also uses deep groundwater for about 19 % of its own supply.

### Estimate (scenario, not validated)

| Item | Value | Basis |
|---|---|---|
| Declared 2023, Kota Semarang | 10.07 Mm³ | ESDM open data |
| Same volume priced at K3-K2 top tier | Rp 112-135 billion/yr | × 11,140-13,429 Rp/m³ |
| Tax per 1 Mm³ undeclared business use | **Rp 8.9-13.4 billion** | K4-K2 top tier |
| Undeclared business use, scenario | 5-15 Mm³/yr | Registered 15-25 Mm³ in 2003-06 and 27.7 in 2018 vs ~10 in 2022-23 |
| Tax at stake | **Rp 45-200 billion/yr** | about 2-10 % of Semarang's 2022 regional tax (Rp 1.93 trillion) |
| Household groundwater (no PDAM) | ~25 Mm³/yr upper bound | PDAM households 41.63 × 38/62. Includes shallow and spring water. |
| Estimated total, Kota cells | 25-48 Mm³ (median 36.5) | demand model, file 07 |
| Estimated total, west+central 16 km cell | 27.9 / 43.8 / 54.7 Mm³ (P10/P50/P90) | validated split, file 09 |

**Honest framing.** The year-to-year swings in registered volume (13.8 vs 27.7 Mm³ one year apart) show the declared series is itself noisy. The "undeclared" scenario mixes three things:
- real decline in pumping since the 2000s;
- under-reporting;
- unregistered wells.

The app must show the range and say which part is which. It must not print a single "lost revenue" number.

### First check to run
Get the realised groundwater tax (PAT) revenue for Kota Semarang, 2020-2025, from the APBD realisation report or LKPJ. Divide it by the declared volume. If the implied Rp per m³ is far below the NPA table, metering or billing is leaking even before any unregistered wells are counted. This needs no satellite data, and it is the strongest single number for the pitch.

---

## B. Inspection leads (new large users in no-new-permit zones)

### What changed after file 14
The first version of B ranked "sinking not explained by permits" as a hunt for illegal wells. File 14 makes that unsound:
- Sinking is soft clay times regional pressure loss.
- Big water users sit on slower ground (X11).
- So unexplained sinking does not mean an illegal well.

B now uses **land change and zoning**, not bowls.

### Facts found
- **The zoning already exists.** Dinas ESDM Jateng mapped the CAT Semarang-Demak conservation zones in 2022 under Permen ESDM 31/2018. The "rusak" (damaged) zone covers most of Kota Semarang.
  - In "kritis" and "rusak" zones, **no new abstraction permit can be issued**.
  - Renewals get 50 % of the previous permitted volume, plus an obligation to build recharge wells.
- **Unregistered wells are the norm, not the exception.** Dinas ESDM Jawa Barat (Jan 2025) counts at least 6,000 well points but only about 200 with a permit, and is remapping wells to raise PAT.
- **Other countries do the same with satellites:**
  - Jordan: Landsat irrigated area vs recorded abstraction found unlicensed wells and wrong meters.
  - Peru, Ica Valley: illicit use about 2× the regulated abstraction (EGU 2024 abstract).
  - EU regulators (IMPEL WODA): optical and SAR methods for illegal abstraction are mature but need local tuning.
  - These are all **irrigation** cases. Urban industrial wells have no ET signal, so we use building change instead.

### Layers
1. Official conservation zones (2022 map; digitise if no GIS file is released).
2. **New large buildings and industrial land since the zone date**, inside kritis/rusak zones: GHSL / Sentinel-2 built-up change, Microsoft or Google building footprints, OSM industrial landuse.
3. **Outside the PDAM network**: a site with no PDAM supply must get water from somewhere, and in a rusak zone it cannot legally be a new well.
4. A lead score of size × water-use class (factory, hotel, mall, hospital) × no PDAM.
5. Field feedback: an inspector marks each lead *registered well / unregistered well / no well / PDAM*. This builds the per-site registry that no open source has (files 12-13), and it measures B's hit rate.

Sinking is shown as context (severity of the zone), never as the locator.

### Validation plan (pre-register before running)
- **Arizona retro test.** ADWR Wells 55 has drill dates and locations (already used in file 05). Does new built/industrial land in year t predict new well registrations within 1 km in t to t+2, against a shift null and a built-matched null? This checks the lead logic where truth exists.
- **Semarang.** Only field feedback or a PPID registry request can validate it. Report hit rate per lead class.

### Limits
- Industrial sites that were already self-supplied before 2022 are not "new", so they are not leads. A covers them, as part of the declared volume.
- The PDAM network map is not public. Kelurahan-level coverage may come from PDAM or a PPID request; without it, layer 3 is a proxy (distance to known mains, SPAM service kecamatan).

---

## C. Pipes instead of pumps

### Facts found
- **SPAM Semarang Barat:**
  - Built as a KPBU (PPP) with PT Air Semarang Barat; raw water from the Jatibarang reservoir (surface water). Design capacity 1,000 L/s (31.5 Mm³/yr).
  - Absorption was 605 L/s in January 2024 (about 19 Mm³/yr), about 44,000 house connections. Target: 70,000 connections in Semarang Barat, Tugu and Ngaliyan.
  - Opened by the President on 23 Jan 2024.
  - That is about twice the whole declared groundwater abstraction of the city.
- **Bangkok:** a groundwater charge plus piped-water expansion, plus a ban on pumping where piped supply exists, cut subsidence to about 0-1 cm/yr in most areas. The gaps were enforcement and household wells, because groundwater was cheaper than piped water.
- **Ho Chi Minh City:** extraction fell from 716,581 to 252,528 m³/day by end 2024 (target 100,000), with SAWACO sealing wells.
- **Jakarta:** Pergub 93/2021 bans groundwater for large buildings in nine zones and 12 road segments from 1 Aug 2023. PAM Jaya coverage is 66-82 % by different reports, with a 100 % target by 2030; enforcement authority is disputed.

### Layers
1. Groundwater demand not served by PDAM: households beyond the network plus self-supplied business. File 07 at 4 km, labelled unvalidated; file 09 at 16 km, validated.
2. Damage potential: soft-clay thickness (file 14, X05/L3).
3. Planned and new supply: SPAM Semarang Barat service kecamatan, other SPAM projects.
4. A ranking with **user-adjustable weights**. The within-city ranking failed validation (file 12), so the app shows its weights and does not claim to predict.

### The experiment that makes C credible (pre-register first)
**Did sinking slow more where SPAM Semarang Barat water arrived?**
- Data already on disk: Sentinel-1 rate maps for 2018-22 and 2023-26 (files 04, 14 X08). File 14 already found a city-wide slowdown, with the fast areas going from 103 to 89 mm/yr; its cause is open.
- Test: a difference-in-differences of the 2023-26 minus 2018-22 rate. Compare Semarang Barat, Tugu and Ngaliyan against other kecamatan with matched clay thickness and built-up level, using a shift null.
- Prediction if pipes help *locally*: a bigger slowdown in the service area.
- Because the pressure loss is regional (file 14), a null result is also informative: it would say the effect spreads over the whole aquifer, so pipe priority should follow volume replaced, not location.
- Caveats:
  - The west has thinner clay (about 20 m) and sinks less, so there is less room to slow.
  - Connections ramped up from 2022 to 2024.
  - Whether the new customers used groundwater before is unknown.

---

## ASEAN scope

| City | Sinking data | Declared abstraction | Piped-water / policy hook |
|---|---|---|---|
| Central Java (35 kab/kota) | LiCSAR 076D/127A on disk for Semarang; other frames free | ESDM open XLSX 2020-23 | Pergub 7/2025 NPA, zone map 2022 |
| Jakarta | LiCSAR (free) | not found yet | Pergub 93/2021 zones, PAM Jaya coverage |
| Ho Chi Minh City | LiCSAR (free) | city totals in the news (716k → 253k m³/day) | SAWACO well sealing |
| Bangkok | LiCSAR (free) | DGR (not checked) | groundwater charge, the success case |
| Manila | LiCSAR (free) | nothing found | not checked |

The MVP covers Central Java fully: A for all kab/kota, B and C for Semarang-Demak. Other cities appear as an A-only comparison where totals exist.

## Challenge fit
- **Organiser:** ASEAN Geospatial Challenge (SLA Singapore / ASEAN portal); BIG runs the Indonesian national round.
- **Theme:** SDGs in general.
- **Judging:** Challenge 20 %, Geospatial Technology 40 %, Communication 20 %, Creativity 20 %.
- **Dates:** the listed timeline (registration 4 Aug to 12 Jan, judging 26 Jan, finals 11 Feb) looks like the cycle now open. Confirm on the official page.
- Geospatial tech is 40 % of the score, so the InSAR pipeline, the validated 16 km split, land-change leads and the pre-registered tests are the core of the pitch. The tax table is what makes it matter.

## MVP (smallest version that tells the story)
- **Static web map:** MapLibre GL, layers as PMTiles / COG built by the existing Python code, no backend.
- **One server-side piece:** the B field-feedback form. A shared table is enough for a demo.
- **Screens:**
  1. A: a Central Java choropleth of declared vs estimated volume and the rupiah gap, with ranges.
  2. B: the Semarang lead map, with a click-through lead card (photo, footprint, zone, PDAM status) and a feedback button.
  3. C: the Semarang/Demak pipe-priority map with weight sliders, plus the SPAM Semarang Barat before/after sinking result.

## To do, in order
1. **Get the PAT realisation** for Kota Semarang 2020-25 (APBD/LKPJ) → first check in A.
2. **Download the ESDM XLSX files** (2020-23) for all kab/kota → A for Central Java.
3. **Pre-register and run the SPAM Semarang Barat test** → C.
4. **Pre-register and run the Arizona new-building → new-well test** → B.
5. **Confirm the household exemption** in UU 1/2022 and the PAT clauses of Perda Semarang 10/2023 (amended by Perda 4/2025).
6. **Digitise the 2022 CAT Semarang-Demak zone map** and get PDAM coverage per kelurahan (PPID request).

## Sources
- Pergub Jateng 7/2025, Penetapan Nilai Perolehan Air Tanah, with annex: [BPK](https://peraturan.bpk.go.id/Details/314690/pergub-prov-jawa-tengah-no-7-tahun-2025)
- Semarang regional tax rates (PAT 20 %): [DDTC News](https://news.ddtc.co.id/berita/daerah/1800913/ketentuan-terbaru-tarif-pajak-daerah-di-kota-semarang-cek-di-sini); Perda 10/2023 on [pasal.id](https://pasal.id/peraturan/perda/perda-kota-semarang-no-10-tahun-2023)
- PAT maximum 20 %: [TERC brief](https://terc.lpem.org/wp-content/uploads/2024/04/PAP_dan_PAT-TERC_Brief.pdf); household exemption (secondary): [enforcea](https://enforcea.com/Blog/apa-itu-pajak-air-tanah)
- Central Java declared volumes: [ESDM dataset](https://data.jatengprov.go.id/dataset/fcc-nilai-perolehan-air-tanah-npa-dan-volume-pengambilan-pengusahaan-air-tanah-di-provinsi-jawa-teng), [use vs availability](https://data.jatengprov.go.id/dataset/29a-persentase-pengambilan-air-tanah-di-jawa-tengah)
- Industry complaints about the NPA rise: [ANTARA, Apr 2026](https://megapolitan.antaranews.com/berita/524333/amdatara-kenaikan-pajak-air-tanah-memberatkan-seluruh-rantai-industri-amdk)
- West Java well remapping (6,000 wells, ~200 permitted): [DDTC News, Jan 2025](https://news.ddtc.co.id/berita/daerah/1808556/demi-kejar-pajak-dinas-esdm-petakan-ulang-sumur-air-tanah-di-daerah)
- CAT Semarang-Demak zones and permit rules: [Undip thesis ch. 1](https://eprints2.undip.ac.id/55333/3/Bab%20I.pdf), [IDX Channel](https://www.idxchannel.com/news/esdm-beberkan-wilayah-yang-cekungan-air-tanahnya-rusak-simak-lokasinya/all)
- SPAM Semarang Barat: [Setkab](https://setkab.go.id/resmikan-spam-semarang-barat-presiden-bantu-masyarakat-peroleh-air-bersih-terjangkau/), [Kemenko Ekon](https://ekon.go.id/unduh/publikasi/4380/pemerintah-dorong-peningkatan-ketersediaan-air-minum-dengan-operasional-psn-spam-semarang-barat), [Investortrust](https://investortrust.id/business/34175/kemenkeu-ungkap-infrastruktur-layanan-air-minum-butuh-investasi-rp-123-5-triliun)
- Bangkok: [Mekong-US Partnership 2020](https://mekonguspartnership.org/2020/10/02/how-bangkok-stopped-sinking-and-what-the-mekong-delta-could-learn-october-2-2020/), [IGES 2009](https://isap.iges.or.jp/2009/jp/pdf/day2/27m_304asiancities.pdf), [World Bank GW-MATE](https://documents1.worldbank.org/curated/en/750761468304831965/pdf/518250BRI0Box31GWMATE1CP1201Bangkok.pdf)
- Ho Chi Minh City: [Tuoi Tre](https://news.tuoitre.vn/ho-chi-minh-city-reduces-groundwater-extraction-to-fight-land-subsidence-10325091712283531.htm)
- Jakarta: [tirto.id](https://tirto.id/gedung-di-zona-bebas-air-tanah-wajib-pakai-air-pam-jaya-g5dF), [Koran Jakarta](https://koran-jakarta.com/2025-09-30/gubernur-dki-jakarta-berkomitmen-kejar-target-cakupan-air-bersih-100-persen/amp)
- Satellite detection of unrecorded abstraction: [Ica Valley, EGU24](https://meetingorganizer.copernicus.org/EGU24/EGU24-11957.html), [Jordan](https://bvbvf1.bib-bvb.de/vufind/PrimoRecord/cdi_proquest_journals_2713850785), [IMPEL WODA](https://impel.eu/contents/libraryfile/FR-2015-11%20WODA%20Final%20Report.pdf)
- Challenge: [ASEAN Geospatial portal](https://www.aseangeospatial.org/asean-geospatial-challenge/), [SLA](https://geospatial.sla.gov.sg/geoworks/asean-geospatial-challenge/)
- Local: Perda Kota Semarang 2024 text (`realdata/semarang/perda/p.txt`), files 07, 09, 12, 13 and 14 of this folder.
