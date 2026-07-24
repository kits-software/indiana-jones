# Imagery and terrain source routing

## Contents

1. Acquisition rules
2. Provider-neutral worldwide flow
3. Open optical and radar sources
4. Elevation and LiDAR
5. Maps and contextual vectors
6. Aerial archives and heritage records
7. Local and user-provided data

## Acquisition rules

- Verify the live endpoint, product version, spatial coverage, licence, attribution, and automated-access terms at acquisition time. URLs and catalog contracts change.
- Prefer source products with stable metadata and machine-readable provenance over screenshots from interactive viewers.
- Download the smallest area and set of bands needed for the stated test.
- Preserve the original product and metadata. Write derived images to a separate directory.
- Record CRS, vertical datum, pixel size, no-data convention, acquisition time, processing level, and resampling.
- Never use a map label, monument overlay, or target coordinate as an input to a supposedly blind detector.

## Provider-neutral worldwide flow

Treat source capabilities separately. A source that can be opened in a browser is not automatically licensed for download, caching, pixel analysis, derived products, model evaluation, or redistribution.

Use this pipeline:

```text
WGS84 AOI
  -> catalog discovery
  -> licence and authorization gate
  -> bounded fetch or local import
  -> checksum and source manifest
  -> orthorectify/reproject to a local metric CRS
  -> modality-specific feature extraction
  -> candidate generation
  -> OSM modern-context review
  -> withheld heritage/known-site unblinding
  -> score and report
```

STAC is the preferred catalog abstraction. It is an [OGC Community Standard](https://www.ogc.org/standards/stac/). The bundled `search-stac` command records a bounded item search but does not download assets or imply that every returned asset permits the intended use.

Worldwide source roles:

| Source | Coverage and role | Automated pixel analysis |
| --- | --- | --- |
| Copernicus Sentinel-1/2 | Global SAR and multispectral time series | Yes, under the current Copernicus terms and product-specific limits |
| USGS Landsat Collection 2 | Global long-term optical and thermal context | Yes; preserve USGS provenance and product metadata |
| Copernicus DEM, NASADEM/SRTM | Global 30 m-class terrain or surface context | Yes, but usually too coarse for subtle banks or ditches |
| OpenTopography | Global catalog plus patchy regional high-resolution topography | Dataset- and account-dependent |
| OpenAerialMap | Patchy worldwide contributed aerial imagery | Yes when the selected image licence permits it |
| National/local portals | Often the best orthophoto or 0.5–2 m LiDAR source | Portal- and dataset-dependent |
| OSM via Overpass | Worldwide vector context and modern-confounder checks | Yes under ODbL; heritage tags remain withheld for blind benchmarks |
| Google Maps/Earth | Bounded interactive reference and permitted attributed captures | Exploratory only when the exact capture/use is permitted; use canonical licensed data for systematic or reproducible analysis |
| User/commercial imagery | Potential worldwide high resolution | Only under the user's recorded rights and provider contract |

## Open optical and radar sources

- [Copernicus Data Space — Sentinel-2](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2): multispectral Level-1C and Level-2A imagery. Use surface reflectance, cloud/shadow masks, native resolutions, and multi-date phenology.
- [Copernicus Data Space — Sentinel-1](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-1): SAR imagery. Calibrate, terrain-correct, and compare consistent orbit, incidence angle, polarization, and season.
- [Copernicus Data Space STAC API](https://documentation.dataspace.copernicus.eu/APIs/STAC.html): machine-readable discovery across available Copernicus collections. Collection names and availability change; enumerate them from the live catalog.
- [USGS EarthExplorer](https://earthexplorer.usgs.gov/): Landsat, aerial, elevation, and other US holdings. Account or product-specific terms may apply.
- [USGS Landsat Collection 2](https://www.usgs.gov/landsat-missions/landsat-collection-2): long time series for landscape-scale context and change.
- [USGS Landsat STAC](https://www.usgs.gov/landsat-missions/spatiotemporal-asset-catalog-stac): official machine-readable discovery for Landsat products.
- [Earth Search](https://github.com/Element84/earth-search): public STAC access to several cloud-hosted Earth-observation collections, including Sentinel-2. Verify the canonical dataset terms and asset provenance.
- [NASA Earthdata](https://www.earthdata.nasa.gov/): global satellite, airborne, and modeled Earth-science holdings with dataset-specific access and use constraints.
- [AWS Open Data Registry](https://registry.opendata.aws/): public cloud mirrors for several Earth-observation products. Confirm the canonical dataset documentation and requester-pays status.

Sentinel-2 and Landsat are not high-resolution site finders. Their strongest archaeological role is large-feature, environmental, land-use, and multi-temporal context.

## Elevation and LiDAR

- [Environment Agency 1 m DTM dataset](https://www.data.gov.uk/dataset/01b3ee39-da3f-47b6-83da-dc98e73a461f/lidar-composite-digital-terrain-model-dtm-1m): near-national England terrain coverage under the stated Open Government Licence terms. The bundled POC uses its WCS endpoint and EPSG:27700.
- [USGS 3D Elevation Program](https://www.usgs.gov/3d-elevation-program): US LiDAR and elevation products.
- [OpenTopography](https://opentopography.org/): research-oriented topography catalog and processing services; dataset access and account requirements vary.
- [Copernicus DEM](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM.html): global GLO-30/GLO-90 surface models. These are DSM products and do not provide worldwide 1 m bare-earth relief.
- [NASA LP DAAC](https://www.earthdata.nasa.gov/centers/lp-daac): NASADEM/SRTM and other global land products. Respect each product's resolution, vertical reference, voids, and use conditions.
- National, regional, and municipal portals may provide classified LAS/LAZ, DTM, or hillshade. Prefer classified point clouds or float terrain models over web-rendered hillshade.

For LiDAR archaeology, inspect point density, classification, flight metadata, no-ground-return areas, and multiple terrain visualizations. A DTM is a model produced by filtering and interpolation, not direct ground truth everywhere.

There is no continuous worldwide 1 m archaeological LiDAR layer. A global 30 m DEM can route landscape-scale research but cannot reproduce the Whitley Castle 1 m terrain POC.

## Maps and contextual vectors

### OpenStreetMap

[OpenStreetMap data is ODbL-licensed](https://www.openstreetmap.org/copyright/). Preserve `© OpenStreetMap contributors`, the licence link, query, timestamp, and bounded AOI. Use Overpass vector data for:

- roads, tracks, rail, buildings, utilities, drains, quarries, mines, land use, water, barriers, and natural-feature negative controls;
- landscape access and modern-change context in a non-operational report;
- post-detection comparison with `historic=*` or `heritage=*` only after candidate generation.

Do not bulk-fetch standard OSM raster tiles. Follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/) and the selected Overpass instance's live limits. OSM incompleteness or a missing heritage tag is not evidence of archaeological absence.

### Google Maps and Google Earth

Do not collapse all Google geospatial products into one rule. The
[Google Earth Additional Terms](https://www.google.com/help/terms_maps-earth/)
govern Earth end-user access and prohibit copying except as Google permits,
mass download, bulk feeds, and substitute datasets. The
[Google Geo guidelines](https://about.google/brand-resource-center/products-and-services/geo-guidelines/)
permit specified attributed Earth uses, including research and educational
contexts, while imposing medium- and product-specific limits. Maps Platform
APIs, Street View, Earth catalog layers, imported data, and generated outputs
have their own applicable terms.

For current Google Earth web navigation, historical imagery, terrain-aware
measurement, catalog/imported data layers, project storage, browser control,
and the required observation record, use the companion
`$research-google-earth` skill and
[google-earth-browser.md](google-earth-browser.md).

Allowed workflow:

1. open the official interface only when the user requests the check;
2. inspect a small area and record visible metadata, a text observation, and a
   safe deep link;
3. retain all Google and third-party attribution;
4. if the current terms permit the capture and intended use, preserve a small
   user-requested capture and run a separately recorded bounded exploratory
   local check;
5. preserve the unaltered capture, file hash, view/date/providers/use basis,
   and separate derived output;
6. do not use hidden endpoints, systematic screenshots, stitching, caching, or
   screen automation to construct a dataset; and
7. switch to licensed AlphaEarth, Sentinel, Landsat, OpenAerialMap, national
   orthophoto, LiDAR, or user-owned imagery for systematic, reproducible,
   training, or evaluation work.

Earth catalog layers remain manual references: inspect their displayed source,
coverage, update date, terms, plan, and experimental status, but do not export
or reconstruct raw catalog data. When a catalog entry links to a canonical
custodian that independently offers a licensed download, acquire and cite it
from that custodian rather than from Earth.

Google Earth Engine is separate from the Google basemap. It can be an optional authenticated compute environment for catalog datasets whose own licences permit the analysis. It requires explicit user authorization and a registered project: [Earth Engine access](https://developers.google.com/earth-engine/guides/access).

AlphaEarth Foundations is also available as canonical Cloud Optimized GeoTIFF
data rather than pixels scraped from the Earth interface. The
[official GCS dataset guide](https://developers.google.com/earth-engine/guides/aef_on_gcs_readme)
states CC BY 4.0 and supplies the required Google/Google DeepMind attribution.
Use that route for licensed local computation and record its provider-pays
access status at retrieval time.

## Aerial archives and heritage records

- [Historic England Aerial Photo Explorer](https://historicengland.org.uk/images-books/archive/collections/aerial-photos/): historical and modern aerial collections for England.
- [Historic England Aerial Archaeology Mapping Explorer](https://historicengland.org.uk/research/results/aerial-archaeology-mapping-explorer/): mapped archaeology derived from aerial photographs and LiDAR. Use as withheld ground truth or corroboration, never as detector input.
- [Archaeology Data Service](https://archaeologydataservice.ac.uk/): project archives, reports, surveys, and datasets with item-specific licences and sensitivity controls.
- National heritage inventories, historic environment records, cadastral maps, geological surveys, and historical map libraries are key corroboration sources.
- Worldwide authoritative examples include [UNESCO Sites Navigator](https://whc.unesco.org/en/wh-gis/), [US National Register downloads](https://www.nps.gov/subjects/nationalregister/data-downloads.htm), [Historic England open data](https://historicengland.org.uk/listing/the-list/data-downloads), and the [Australian Heritage Database](https://www.dcceew.gov.au/parks-heritage/heritage/publications/australian-heritage-database). Many inventories deliberately generalize or omit vulnerable places.

Archive imagery is opportunistic. Absence from the archive, or from one season, is not site absence.

## Local and user-provided data

For local rasters, photographs, PDFs, maps, books, or exported social posts:

1. hash the original;
2. record who supplied it and what use was authorized;
3. preserve EXIF/sidecar metadata separately;
4. avoid uploading or redistributing private material;
5. crop or redact personal and precise site information in public outputs;
6. note when compression, screenshots, unknown scale, or missing provenance limit interpretation.

Use authenticated browser access only under the case-specific workflow in `ethics-and-web-research.md`.

The bundled `register-raster` sidecar binds declared bbox/CRS/licence metadata to a SHA-256, but it does not parse the GeoTIFF geotransform. Verify spatial metadata externally before registration. Keep credentials out of case ledgers and use environment variables or the provider's authorized client when an optional source needs authentication.
