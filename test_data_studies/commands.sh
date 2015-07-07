#!/bin/bash -xe

export PGDATESTYLE="ISO, MDY"

studies=`ls test_data_studies/studies`

echo "DROPPING ENV... "
qiita-env drop --no-ask-for-confirmation
echo "Ok"

echo "MAKING ENV... "
qiita-env make --add-demo-user --no-load-ontologies
echo "Ok"

# Inserting all the information for each study
echo "INSERTING STUDIES"
mkdir -p temp
for i in ${studies[@]}; do
    # Get all needed filepaths for the study
    conf_fp=test_data_studies/studies/$i/study_config.txt
    sample_file=test_data_studies/studies/$i/sample_template_$i.txt
    prep_file=test_data_studies/studies/$i/prep_template_$i.txt
    otu_table=test_data_studies/studies/$i/otu_table.biom

    echo "Study $i:"
    # Generate the study config file
    echo "\tgenerating config file... "
    title=`awk -F '\t' -v col=TITLE 'NR==1{for(i=1;i<=NF;i++){if($i==col){c=i;break}} print $c} NR>1{print $c}' ${sample_file} | sort | uniq | grep -vw TITLE | head -n 1`
    echo -e "[required]\ntimeseries_type_id = 1\nmetadata_complete = True\nmixs_compliant = True\nprincipal_investigator = Earth Microbiome Project, emp@earthmicrobiome.org, UCSD\nreprocess = False\nstudy_alias = $title\nstudy_description = $description\nstudy_abstract = $description\nefo_ids = 1\n[optional]\nstudy_id = $i" > $conf_fp
    echo "Ok"

    # Insert the study
    echo "\tloading study... "
    output="`qiita db load_study --owner demo@microbio.me --title "$title" --info $conf_fp`"
    study_id=`echo -e "${output}" | cut -d " " -f 9`
    echo "Ok"

    # Insert the sample template
    echo "\tloading sample template... "
    qiita db load_sample_template $sample_file --study $study_id
    echo "Ok"

    # Loading prep template
    echo "\tloading prep template... "
    output=`qiita db load_prep_template $prep_file --study $study_id --data_type "16S"`
    pt_id=`echo -e "${output}" | cut -d " " -f 10`
    echo "Ok"

    # Loading raw data
    echo "\tloading raw data... "
    echo -e ">seq\nAAAA" > seqs.fna
    output="`qiita db load_raw --fp seqs.fna --fp_type raw_forward_seqs --filetype FASTQ --prep_template $pt_id`"
    raw_id=`echo -e "${output}" | cut -d " " -f 10`
    echo "Ok"

    # Loading preprocessed data
    echo "\tloading preprocessed data... "
    echo -e ">seq\nAAAA" > temp/seqs.fna
    output=`qiita db load_preprocessed --study_id $study_id --params_table preprocessed_sequence_454_params --filedir temp/ --filepathtype preprocessed_fasta --params_id 1 --prep_template_id $pt_id`
    ppd_id=`echo -e "${output}" | cut -d " " -f 10`
    echo "Ok"

    # Loading processed data
    echo "\tloading processed data... "
    cp $otu_table ${otu_table}_backup
    output="`qiita db load_processed --fp $otu_table --fp_type biom --processed_params_table processed_params_sortmerna --processed_params_id 1 --preprocessed_data_id ${ppd_id}`"
    pd_id=`echo -e "${output}" | cut -d " " -f 10`
    mv ${otu_table}_backup $otu_table
    echo "Ok"

    # Making study public by making its processed data public
    echo "\tmaking study public... "
    echo -e "from qiita_db.data import ProcessedData\nProcessedData(${pd_id}).status = 'public'\n\n" | python
    echo "Ok"
    rm $conf_fp
done
rmdir temp
