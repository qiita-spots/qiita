from unittest import main

from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestRedbiom(TestHandlerBase):

    def test_get(self):
        response = self.get('/redbiom/')
        self.assertEqual(response.code, 200)

    def test_post_metadata(self):
        post_args = {
            'context': 'test',
            'search': 'infant',
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success', 'message': '', 'data': OBSERVATION_HTML}
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'context': 'test',
            'search': 'inf',
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': 'No samples where found! Try again ...', 'data': ''}
        self.assertEqual(loads(response.body), exp)

    def test_post_sequence(self):
        post_args = {
            'context': 'test',
            'search': ('TACGTAGGGGGCAAGCGTTATCCGGATTTACTGGGTGTAAAGGGAGCGTAGAC'
                       'GGCTGTACAAGTCTGAAGTGAAAGGCATGGGCTCAACCTGTGGACTG'),
            'search_on': 'observations'
        }
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success', 'message': '', 'data': SEQUENCE_HTML}
        loads(response.body)
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'context': 'test',
            'search': ('TT'),
            'search_on': 'observations'
        }
        response = self.post('/redbiom/', post_args)
        exp = {'status': 'success',
               'message': 'No samples where found! Try again ...', 'data': ''}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

    def test_post_errors(self):
        post_args = {
            'context': 'should error',
            'search': 'infant',
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': ("The given context is not valid: should error - "
                           "[u'test' u'test-alt']"),
               'data': ''}
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'context': 'test',
            'search_on': 'metadata'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success', 'message': "Nothing to search for ...",
               'data': ''}
        self.assertEqual(loads(response.body), exp)

        post_args = {
            'context': 'test',
            'search': 'infant',
            'search_on': 'error'
        }
        response = self.post('/redbiom/', post_args)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success',
               'message': 'Not a valid option for search_on', 'data': ''}
        self.assertEqual(loads(response.body), exp)


OBSERVATION_HTML = """<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>#SampleID</th>
      <th>ACID_REFLUX</th>
      <th>ACNE_MEDICATION</th>
      <th>ACNE_MEDICATION_OTC</th>
      <th>ADD_ADHD</th>
      <th>AGE_CAT</th>
      <th>AGE_CORRECTED</th>
      <th>AGE_YEARS</th>
      <th>ALCOHOL_CONSUMPTION</th>
      <th>ALCOHOL_FREQUENCY</th>
      <th>ALCOHOL_TYPES_BEERCIDER</th>
      <th>ALCOHOL_TYPES_RED_WINE</th>
      <th>ALCOHOL_TYPES_SOUR_BEERS</th>
      <th>ALCOHOL_TYPES_SPIRITSHARD_ALCOHOL</th>
      <th>ALCOHOL_TYPES_UNSPECIFIED</th>
      <th>ALCOHOL_TYPES_WHITE_WINE</th>
      <th>ALLERGIC_TO_I_HAVE_NO_FOOD_ALLERGIES_THAT_I_KNOW_OF</th>
      <th>ALLERGIC_TO_OTHER</th>
      <th>ALLERGIC_TO_PEANUTS</th>
      <th>ALLERGIC_TO_SHELLFISH</th>
      <th>ALLERGIC_TO_TREE_NUTS</th>
      <th>ALLERGIC_TO_UNSPECIFIED</th>
      <th>ALTITUDE</th>
      <th>ALZHEIMERS</th>
      <th>ANONYMIZED_NAME</th>
      <th>ANTIBIOTIC_HISTORY</th>
      <th>APPENDIX_REMOVED</th>
      <th>ARTIFICIAL_SWEETENERS</th>
      <th>ASD</th>
      <th>ASSIGNED_FROM_GEO</th>
      <th>AUTOIMMUNE</th>
      <th>BIRTH_YEAR</th>
      <th>BMI</th>
      <th>BMI_CAT</th>
      <th>BMI_CORRECTED</th>
      <th>BODY_HABITAT</th>
      <th>BODY_PRODUCT</th>
      <th>BODY_SITE</th>
      <th>BOWEL_MOVEMENT_FREQUENCY</th>
      <th>BOWEL_MOVEMENT_QUALITY</th>
      <th>BREASTMILK_FORMULA_ENSURE</th>
      <th>BarcodeSequence</th>
      <th>CANCER</th>
      <th>CARDIOVASCULAR_DISEASE</th>
      <th>CAT</th>
      <th>CDIFF</th>
      <th>CENTER_NAME</th>
      <th>CENTER_PROJECT_NAME</th>
      <th>CHICKENPOX</th>
      <th>CLINICAL_CONDITION</th>
      <th>COLLECTION_MONTH</th>
      <th>COLLECTION_SEASON</th>
      <th>COLLECTION_TIME</th>
      <th>COMMON_NAME</th>
      <th>CONSUME_ANIMAL_PRODUCTS_ABX</th>
      <th>CONTRACEPTIVE</th>
      <th>COSMETICS_FREQUENCY</th>
      <th>COUNTRY</th>
      <th>COUNTRY_OF_BIRTH</th>
      <th>COUNTRY_RESIDENCE</th>
      <th>CSECTION</th>
      <th>DEODORANT_USE</th>
      <th>DEPTH</th>
      <th>DIABETES</th>
      <th>DIET_TYPE</th>
      <th>DNA_EXTRACTED</th>
      <th>DOG</th>
      <th>DOMINANT_HAND</th>
      <th>DRINKING_WATER_SOURCE</th>
      <th>Description</th>
      <th>ELEVATION</th>
      <th>ENV_BIOME</th>
      <th>ENV_FEATURE</th>
      <th>ENV_MATERIAL</th>
      <th>ENV_MATTER</th>
      <th>ENV_PACKAGE</th>
      <th>EPILEPSY_OR_SEIZURE_DISORDER</th>
      <th>EXERCISE_LOCATION</th>
      <th>EXPERIMENT_CENTER</th>
      <th>EXPERIMENT_DESIGN_DESCRIPTION</th>
      <th>EXPERIMENT_TITLE</th>
      <th>EXTRACTIONKIT_LOT</th>
      <th>EXTRACTION_ROBOT</th>
      <th>FED_AS_INFANT</th>
      <th>FERMENTED_PLANT_FREQUENCY</th>
      <th>FLU_VACCINE_DATE</th>
      <th>FROZEN_DESSERT_FREQUENCY</th>
      <th>FRUIT_FREQUENCY</th>
      <th>FUNGAL_OVERGROWTH</th>
      <th>GEO_LOC_NAME</th>
      <th>GLUTEN</th>
      <th>HAS_PHYSICAL_SPECIMEN</th>
      <th>HEIGHT_CM</th>
      <th>HEIGHT_UNITS</th>
      <th>HIGH_FAT_RED_MEAT_FREQUENCY</th>
      <th>HMP_SITE</th>
      <th>HOMECOOKED_MEALS_FREQUENCY</th>
      <th>HOST_COMMON_NAME</th>
      <th>HOST_SUBJECT_ID</th>
      <th>HOST_TAXID</th>
      <th>IBD</th>
      <th>IBS</th>
      <th>INSTRUMENT_MODEL</th>
      <th>KIDNEY_DISEASE</th>
      <th>LACTOSE</th>
      <th>LAST_MOVE</th>
      <th>LAST_TRAVEL</th>
      <th>LATITUDE</th>
      <th>LEVEL_OF_EDUCATION</th>
      <th>LIBRARY_CONSTRUCTION_PROTOCOL</th>
      <th>LINKER</th>
      <th>LIVER_DISEASE</th>
      <th>LIVINGWITH</th>
      <th>LONGITUDE</th>
      <th>LOWGRAIN_DIET_TYPE</th>
      <th>LUNG_DISEASE</th>
      <th>LinkerPrimerSequence</th>
      <th>MASTERMIX_LOT</th>
      <th>MENTAL_ILLNESS</th>
      <th>MENTAL_ILLNESS_TYPE_ANOREXIA_NERVOSA</th>
      <th>MENTAL_ILLNESS_TYPE_BIPOLAR_DISORDER</th>
      <th>MENTAL_ILLNESS_TYPE_BULIMIA_NERVOSA</th>
      <th>MENTAL_ILLNESS_TYPE_DEPRESSION</th>
      <th>MENTAL_ILLNESS_TYPE_PTSD_POSTTRAUMATIC_STRESS_DISORDER</th>
      <th>MENTAL_ILLNESS_TYPE_SCHIZOPHRENIA</th>
      <th>MENTAL_ILLNESS_TYPE_SUBSTANCE_ABUSE</th>
      <th>MENTAL_ILLNESS_TYPE_UNSPECIFIED</th>
      <th>MIGRAINE</th>
      <th>MILK_CHEESE_FREQUENCY</th>
      <th>MILK_SUBSTITUTE_FREQUENCY</th>
      <th>MULTIVITAMIN</th>
      <th>NAIL_BITER</th>
      <th>NON_FOOD_ALLERGIES_BEESTINGS</th>
      <th>NON_FOOD_ALLERGIES_DRUG_EG_PENICILLIN</th>
      <th>NON_FOOD_ALLERGIES_PET_DANDER</th>
      <th>NON_FOOD_ALLERGIES_POISON_IVYOAK</th>
      <th>NON_FOOD_ALLERGIES_SUN</th>
      <th>NON_FOOD_ALLERGIES_UNSPECIFIED</th>
      <th>ORIG_NAME</th>
      <th>OTHER_SUPPLEMENT_FREQUENCY</th>
      <th>PCR_PRIMERS</th>
      <th>PETS_OTHER</th>
      <th>PETS_OTHER_FREETEXT</th>
      <th>PHYSICAL_SPECIMEN_LOCATION</th>
      <th>PHYSICAL_SPECIMEN_REMAINING</th>
      <th>PKU</th>
      <th>PLATFORM</th>
      <th>PLATING</th>
      <th>POOL_FREQUENCY</th>
      <th>PREGNANT</th>
      <th>PRIMER_DATE</th>
      <th>PRIMER_PLATE</th>
      <th>PROBIOTIC_FREQUENCY</th>
      <th>PROCESSING_ROBOT</th>
      <th>PROJECT_NAME</th>
      <th>PUBLIC</th>
      <th>RACE</th>
      <th>READY_TO_EAT_MEALS_FREQUENCY</th>
      <th>REQUIRED_SAMPLE_INFO_STATUS</th>
      <th>RUN_CENTER</th>
      <th>RUN_PREFIX</th>
      <th>SAMPLE_PLATE</th>
      <th>SAMPLE_TYPE</th>
      <th>SAMP_SIZE</th>
      <th>SCIENTIFIC_NAME</th>
      <th>SEASONAL_ALLERGIES</th>
      <th>SEQUENCING_METH</th>
      <th>SEX</th>
      <th>SIBO</th>
      <th>SIMPLE_BODY_SITE</th>
      <th>SKIN_CONDITION</th>
      <th>SLEEP_DURATION</th>
      <th>SMOKING_FREQUENCY</th>
      <th>SOFTENER</th>
      <th>SUBSET_AGE</th>
      <th>SUBSET_ANTIBIOTIC_HISTORY</th>
      <th>SUBSET_BMI</th>
      <th>SUBSET_DIABETES</th>
      <th>SUBSET_HEALTHY</th>
      <th>SUBSET_IBD</th>
      <th>SUGARY_SWEETS_FREQUENCY</th>
      <th>SUGAR_SWEETENED_DRINK_FREQUENCY</th>
      <th>SURVEY_ID</th>
      <th>TARGET_GENE</th>
      <th>TARGET_SUBFRAGMENT</th>
      <th>TAXON_ID</th>
      <th>TEETHBRUSHING_FREQUENCY</th>
      <th>THYROID</th>
      <th>TITLE</th>
      <th>TITLE_ACRONYM</th>
      <th>TITLE_BODY_SITE</th>
      <th>TM1000_8_TOOL</th>
      <th>TM300_8_TOOL</th>
      <th>TM50_8_TOOL</th>
      <th>TONSILS_REMOVED</th>
      <th>TYPES_OF_PLANTS</th>
      <th>VEGETABLE_FREQUENCY</th>
      <th>WATER_LOT</th>
      <th>WEIGHT_CHANGE</th>
      <th>WEIGHT_KG</th>
      <th>WEIGHT_UNITS</th>
      <th>WELL_DESCRIPTION</th>
      <th>WELL_ID</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>UNTAGGED_10317.000047188</th>
      <td>10317.000047188.UNTAGGED</td>
      <td>I do not have this condition</td>
      <td>No</td>
      <td>No</td>
      <td>I do not have this condition</td>
      <td>50s</td>
      <td>59.0</td>
      <td>59</td>
      <td>No</td>
      <td>Never</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>Yes</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>Yes</td>
      <td>0</td>
      <td>I do not have this condition</td>
      <td>000047188</td>
      <td>I have not taken antibiotics in the past year.</td>
      <td>No</td>
      <td>Never</td>
      <td>I do not have this condition</td>
      <td>Yes</td>
      <td>I do not have this condition</td>
      <td>1957</td>
      <td>22.55</td>
      <td>Normal</td>
      <td>22.55</td>
      <td>UBERON:feces</td>
      <td>UBERON:feces</td>
      <td>UBERON:feces</td>
      <td>Two</td>
      <td>I tend to have normal formed stool - Type 3 and 4</td>
      <td>No</td>
      <td>TTGGACGTCCAC</td>
      <td>I do not have this condition</td>
      <td>I do not have this condition</td>
      <td>No</td>
      <td>I do not have this condition</td>
      <td>UCSDMI</td>
      <td>AG32</td>
      <td>Yes</td>
      <td>I do not have this condition</td>
      <td>May</td>
      <td>Spring</td>
      <td>11:00</td>
      <td>human gut metagenome</td>
      <td>Not sure</td>
      <td>No</td>
      <td>Never</td>
      <td>United Kingdom</td>
      <td>United Kingdom</td>
      <td>United Kingdom</td>
      <td>No</td>
      <td>I do not use deodorant or an antiperspirant</td>
      <td>0</td>
      <td>I do not have this condition</td>
      <td>Omnivore</td>
      <td>Yes</td>
      <td>Yes</td>
      <td>I am right handed</td>
      <td>City</td>
      <td>American Gut Project Stool sample</td>
      <td>75.4</td>
      <td>dense settlement biome</td>
      <td>human-associated habitat</td>
      <td>feces</td>
      <td>ENVO:feces</td>
      <td>human-gut</td>
      <td>I do not have this condition</td>
      <td>Both</td>
      <td>UCSDMI</td>
      <td>fecal, saliva, skin and environment samples fr...</td>
      <td>American Gut Project</td>
      <td>PM16F14</td>
      <td>HOWE_KF3</td>
      <td>Primarily infant formula</td>
      <td>Never</td>
      <td>I have not gotten the flu vaccine in the past ...</td>
      <td>Never</td>
      <td>Daily</td>
      <td>I do not have this condition</td>
      <td>United Kingdom:Unspecified</td>
      <td>No</td>
      <td>Yes</td>
      <td>170</td>
      <td>centimeters</td>
      <td>Never</td>
      <td>FECAL</td>
      <td>Daily</td>
      <td>human</td>
      <td>7b903658b298639ac5ff12dc065b208ff0862c47509fdb...</td>
      <td>9606</td>
      <td>I do not have this condition</td>
      <td>I do not have this condition</td>
      <td>Illumina MiSeq</td>
      <td>I do not have this condition</td>
      <td>No</td>
      <td>I have lived in my current state of residence ...</td>
      <td>I have not been outside of my country of resid...</td>
      <td>50.6</td>
      <td>Graduate or Professional degree</td>
      <td>Illumina MiSeq 515fbc, 806r amplification of 1...</td>
      <td>GT</td>
      <td>I do not have this condition</td>
      <td>No</td>
      <td>-3.5</td>
      <td>Yes</td>
      <td>I do not have this condition</td>
      <td>GTGTGCCAGCMGCCGCGGTAA</td>
      <td>373139</td>
      <td>No</td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>I do not have this condition</td>
      <td>Daily</td>
      <td>Never</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>No</td>
      <td>Yes</td>
      <td>47188</td>
      <td>No</td>
      <td>FWD:GTGYCAGCMGCCGCGGTAA; REV:GGACTACNVGGGTWTCTAAT</td>
      <td>No</td>
      <td></td>
      <td>UCSDMI</td>
      <td>Yes</td>
      <td>I do not have this condition</td>
      <td>Illumina</td>
      <td>LDG</td>
      <td>Never</td>
      <td>No</td>
      <td>71416</td>
      <td>5</td>
      <td>Daily</td>
      <td>JERE</td>
      <td>AGP</td>
      <td>Yes</td>
      <td>Caucasian</td>
      <td>Never</td>
      <td>completed</td>
      <td>UCSDMI</td>
      <td>AG32_S1_L001</td>
      <td>AG_140</td>
      <td>Stool</td>
      <td>0.1,g</td>
      <td>human gut metagenome</td>
      <td>No</td>
      <td>Sequencing by synthesis</td>
      <td>female</td>
      <td>I do not have this condition</td>
      <td>FECAL</td>
      <td>I do not have this condition</td>
      <td>6-7 hours</td>
      <td>Never</td>
      <td>Yes</td>
      <td>True</td>
      <td>True</td>
      <td>True</td>
      <td>True</td>
      <td>True</td>
      <td>True</td>
      <td>Never</td>
      <td>Never</td>
      <td>6d98dc83ed2451c1</td>
      <td>16S rRNA</td>
      <td>V4</td>
      <td>408170</td>
      <td>Daily</td>
      <td>I do not have this condition</td>
      <td>American Gut Project</td>
      <td>AGP</td>
      <td>AGP-FECAL</td>
      <td>108379Z</td>
      <td>109375A</td>
      <td>311441B</td>
      <td>No</td>
      <td>6 to 10</td>
      <td>Daily</td>
      <td>RNBF2734</td>
      <td>Remained stable</td>
      <td>65</td>
      <td>kilograms</td>
      <td>AG_140_47188_F9</td>
      <td>F9</td>
    </tr>
  </tbody>
</table>"""


SEQUENCE_HTML = """<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>#SampleID</th>
      <th>ACNE_MEDICATION</th>
      <th>ACNE_MEDICATION_OTC</th>
      <th>AGE_CAT</th>
      <th>AGE_CORRECTED</th>
      <th>AGE_YEARS</th>
      <th>ALCOHOL_CONSUMPTION</th>
      <th>ALCOHOL_TYPES_BEERCIDER</th>
      <th>ALCOHOL_TYPES_RED_WINE</th>
      <th>ALCOHOL_TYPES_SOUR_BEERS</th>
      <th>ALCOHOL_TYPES_SPIRITSHARD_ALCOHOL</th>
      <th>ALCOHOL_TYPES_UNSPECIFIED</th>
      <th>ALCOHOL_TYPES_WHITE_WINE</th>
      <th>ALLERGIC_TO_I_HAVE_NO_FOOD_ALLERGIES_THAT_I_KNOW_OF</th>
      <th>ALLERGIC_TO_OTHER</th>
      <th>ALLERGIC_TO_PEANUTS</th>
      <th>ALLERGIC_TO_SHELLFISH</th>
      <th>ALLERGIC_TO_TREE_NUTS</th>
      <th>ALLERGIC_TO_UNSPECIFIED</th>
      <th>ALTITUDE</th>
      <th>ANONYMIZED_NAME</th>
      <th>ANTIBIOTIC_HISTORY</th>
      <th>APPENDIX_REMOVED</th>
      <th>ASSIGNED_FROM_GEO</th>
      <th>BIRTH_YEAR</th>
      <th>BMI</th>
      <th>BMI_CAT</th>
      <th>BODY_HABITAT</th>
      <th>BODY_PRODUCT</th>
      <th>BODY_SITE</th>
      <th>CAT</th>
      <th>CENSUS_REGION</th>
      <th>CHICKENPOX</th>
      <th>COLLECTION_MONTH</th>
      <th>COLLECTION_SEASON</th>
      <th>COLLECTION_TIME</th>
      <th>COMMON_NAME</th>
      <th>COUNTRY</th>
      <th>COUNTRY_OF_BIRTH</th>
      <th>CSECTION</th>
      <th>DEODORANT_USE</th>
      <th>DEPTH</th>
      <th>DIABETES</th>
      <th>DIET_TYPE</th>
      <th>DNA_EXTRACTED</th>
      <th>DOG</th>
      <th>DOMINANT_HAND</th>
      <th>DRINKING_WATER_SOURCE</th>
      <th>Description</th>
      <th>ECONOMIC_REGION</th>
      <th>ELEVATION</th>
      <th>ENA-BASE-COUNT</th>
      <th>ENA-CHECKLIST</th>
      <th>ENA-SPOT-COUNT</th>
      <th>ENV_BIOME</th>
      <th>ENV_FEATURE</th>
      <th>ENV_MATTER</th>
      <th>EXERCISE_LOCATION</th>
      <th>FLU_VACCINE_DATE</th>
      <th>GLUTEN</th>
      <th>HAS_PHYSICAL_SPECIMEN</th>
      <th>HEIGHT_CM</th>
      <th>HEIGHT_UNITS</th>
      <th>HMP_SITE</th>
      <th>HOST_COMMON_NAME</th>
      <th>HOST_SUBJECT_ID</th>
      <th>HOST_TAXID</th>
      <th>IBD</th>
      <th>LACTOSE</th>
      <th>LAST_TRAVEL</th>
      <th>LATITUDE</th>
      <th>LIVINGWITH</th>
      <th>LONGITUDE</th>
      <th>LUNG_DISEASE</th>
      <th>MIGRAINE</th>
      <th>MULTIVITAMIN</th>
      <th>NAIL_BITER</th>
      <th>NON_FOOD_ALLERGIES_BEESTINGS</th>
      <th>NON_FOOD_ALLERGIES_DRUG_EG_PENICILLIN</th>
      <th>NON_FOOD_ALLERGIES_PET_DANDER</th>
      <th>NON_FOOD_ALLERGIES_POISON_IVYOAK</th>
      <th>NON_FOOD_ALLERGIES_SUN</th>
      <th>NON_FOOD_ALLERGIES_UNSPECIFIED</th>
      <th>OTHER_SUPPLEMENT_FREQUENCY</th>
      <th>PHYSICAL_SPECIMEN_LOCATION</th>
      <th>PHYSICAL_SPECIMEN_REMAINING</th>
      <th>PKU</th>
      <th>POOL_FREQUENCY</th>
      <th>PREGNANT</th>
      <th>PUBLIC</th>
      <th>RACE</th>
      <th>REQUIRED_SAMPLE_INFO_STATUS</th>
      <th>SAMPLE_TYPE</th>
      <th>SEASONAL_ALLERGIES</th>
      <th>SEX</th>
      <th>SIMPLE_BODY_SITE</th>
      <th>SKIN_CONDITION</th>
      <th>SLEEP_DURATION</th>
      <th>SMOKING_FREQUENCY</th>
      <th>SOFTENER</th>
      <th>STATE</th>
      <th>SUBSET_AGE</th>
      <th>SUBSET_ANTIBIOTIC_HISTORY</th>
      <th>SUBSET_BMI</th>
      <th>SUBSET_DIABETES</th>
      <th>SUBSET_HEALTHY</th>
      <th>SUBSET_IBD</th>
      <th>SURVEY_ID</th>
      <th>TEETHBRUSHING_FREQUENCY</th>
      <th>TITLE</th>
      <th>TITLE_ACRONYM</th>
      <th>TITLE_BODY_SITE</th>
      <th>TONSILS_REMOVED</th>
      <th>TYPES_OF_PLANTS</th>
      <th>WEIGHT_CHANGE</th>
      <th>WEIGHT_KG</th>
      <th>WEIGHT_UNITS</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>UNTAGGED_10317.000012975</th>
      <td>10317.000012975.UNTAGGED</td>
      <td>false</td>
      <td>false</td>
      <td>40s</td>
      <td>48.0</td>
      <td>48.0</td>
      <td>true</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>true</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>true</td>
      <td>0</td>
      <td>000012975</td>
      <td>Year</td>
      <td>No</td>
      <td>True</td>
      <td>1966.0</td>
      <td>21.67</td>
      <td>Normal</td>
      <td>UBERON:feces</td>
      <td>UBERON:feces</td>
      <td>UBERON:feces</td>
      <td>true</td>
      <td>Northeast</td>
      <td>Yes</td>
      <td>January</td>
      <td>Winter</td>
      <td>09:00</td>
      <td>human gut metagenome</td>
      <td>USA</td>
      <td>United States</td>
      <td>No</td>
      <td>I use an antiperspirant</td>
      <td>0.0</td>
      <td>I do not have this condition</td>
      <td>Omnivore</td>
      <td>True</td>
      <td>false</td>
      <td>I am right handed</td>
      <td>City</td>
      <td>American Gut Project Stool sample</td>
      <td>New England</td>
      <td>3.5</td>
      <td>2219398</td>
      <td>ERC000011</td>
      <td>14698</td>
      <td>ENVO:dense settlement biome</td>
      <td>ENVO:human-associated habitat</td>
      <td>ENVO:feces</td>
      <td>Depends on the season</td>
      <td>I have not gotten the flu vaccine in the past ...</td>
      <td>No</td>
      <td>True</td>
      <td>165.0</td>
      <td>centimeters</td>
      <td>FECAL</td>
      <td>human</td>
      <td>2173b2f00a5b125e8d3b92856d7fb3273ee4e9feb545f6...</td>
      <td>9606</td>
      <td>I do not have this condition</td>
      <td>false</td>
      <td>I have not been outside of my country of resid...</td>
      <td>42.4</td>
      <td>No</td>
      <td>-71.2</td>
      <td>I do not have this condition</td>
      <td>I do not have this condition</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>false</td>
      <td>true</td>
      <td>true</td>
      <td>UCSDMI</td>
      <td>True</td>
      <td>I do not have this condition</td>
      <td>Never</td>
      <td>No</td>
      <td>True</td>
      <td>Other</td>
      <td>completed</td>
      <td>Stool</td>
      <td>false</td>
      <td>female</td>
      <td>FECAL</td>
      <td>I do not have this condition</td>
      <td>6-7 hours</td>
      <td>Never</td>
      <td>true</td>
      <td>MA</td>
      <td>true</td>
      <td>false</td>
      <td>true</td>
      <td>true</td>
      <td>false</td>
      <td>true</td>
      <td>d9d96de7461c00b6</td>
      <td>Daily</td>
      <td>American Gut Project</td>
      <td>AGP</td>
      <td>AGP-FECAL</td>
      <td>No</td>
      <td>More than 30</td>
      <td>Increased more than 10 pounds</td>
      <td>59.0</td>
      <td>kilograms</td>
    </tr>
  </tbody>
</table>"""

if __name__ == "__main__":
    main()
