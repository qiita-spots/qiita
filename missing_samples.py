from qiita_db.study import Study
from biom import load_table

studies = Study.get_by_status('private').union(
    Study.get_by_status('public')).union(Study.get_by_status('sandbox'))

to_fix = {}
for study in studies:
    if study.sample_template is None:
        continue
    sids = list(study.sample_template.keys())
    for a in study.artifacts(artifact_type='BIOM'):
        for fid, fp, fpt in a.filepaths:
            if fpt == 'biom':
                try:
                    biom_table = load_table(fp)
                    biom_samples = biom_table.ids()
                except:
                    biom_samples = []
                if not set(biom_samples).issubset(set(sids)):
                    if study not in to_fix:
                        to_fix[study] = {}
                    if a not in to_fix[study]:
                        to_fix[study][a] = []
                    to_fix[study][a].append(fp)


Fix
{(808,
  'NEON: Directions and resources for long-term monitoring in soil microbial ecology',
  'public'),
 (864,
  'Space, time and change: Investigations of soil bacterial diversity and its drivers in the Mongolian steppe',
  'public'),
 (894, 'Catchment sources of microbes', 'public'),
 (926,
  'Seasonal restructuring of the ground squirrel gut microbiota over the annual hibernation cycle',
  'public'),
 (1036,
  ' Microbial communities of the deep unfrozen: Do microbes in taliks increase permafrost carbon vulnerability?',
  'public'),
 (1717,
  'Agricultural intensification and the functional capacity of soil microbes on smallholder African farms -swkenya',
  'public'),
 (1773,
  'Characterization of bird gut microbiome - gizzard, upper intestine, lower intestine from birds in Venezuela',
  'public'),
 (1883,
  'Microbial diversity in arctic freshwaters is structured by inoculation of microbes from soils',
  'public'),
 (10293,
  'Impact of freeze-drying on milk oligosaccharide content and marker gene bacterial community profiles in infant fecal samples',
  'public'),


Delete
 (1970, 'American Gut - best/worst', 'private'),
 (2006, 'American Gut 3', 'private'),

Check status
 (10138, 'Pitcher plant chronosequence', 'sandbox'), -- duplicated ???
didn't start from raw
 (10390, 'Integrative Human Microbiome Project (Pilot Data)', 'sandbox'),
 (10462, 'Rana sierrae skin microbiome at the SF Zoo', 'private'),
 (10510,
  'Fungal diversity comparison between Antarctic and Joshua Tree
National Park rocks',
  'private'),
   (10539,
  'Temporal and spatial variation of the human microbiota during pregnancy.',
  'sandbox'),
 (10584, 'Holland, MI Floodplains', 'sandbox'),
 (10699, 'pox time series', 'sandbox')}
