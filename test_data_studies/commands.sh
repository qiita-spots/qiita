#!/bin/bash -xe

export PGDATESTYLE="ISO, MDY"

studies=`ls test_data_studies/studies`

echo "DROPPING ENV... "
qiita_env drop --no-ask-for-confirmation
echo "Ok"

echo "MAKING ENV... "
qiita_env make --add-demo-user --no-load-ontologies # --download-reference
echo "Ok"

# Inserting all the information for each study
echo "INSERTING STUDIES"
base_id=0
for i in ${studies[@]}; do
    base_id=$((base_id+1))
    # Get all needed filepaths for the study
    conf_fp=test_data_studies/studies/$i/study_config.txt
    sample_file=test_data_studies/studies/$i/sample_template_$i.txt
    prep_file=test_data_studies/studies/$i/prep_template_$i.txt
    otu_table=test_data_studies/studies/$i/otu_table.biom

    echo "Study $i:"
    # Generate the study config file
    echo "\tgenerating config file... "
    echo -e "[required]\ntimeseries_type_id = 1\nmetadata_complete = True\nmixs_compliant = True\nportal_type_id = 3\nprincipal_investigator = Earth Microbiome Project, emp@earthmicrobiome.org, CU Boulder\nreprocess = False\nstudy_alias = $title\nstudy_description = $description\nstudy_abstract = $description\nefo_ids = 1\n[optional]\nstudy_id = $i" > $conf_fp
    echo "Ok"

    # Insert the study
    echo "\tloading study... "
    title=`awk -F '\t' -v col=TITLE 'NR==1{for(i=1;i<=NF;i++){if($i==col){c=i;break}} print $c} NR>1{print $c}' ${sample_file} | sort | uniq | grep -vw TITLE | head -n 1`
    qiita db load_study --owner demo@microbio.me --title "$title" --info $conf_fp
    echo "Ok"

    # Insert the sample template
    echo "\tloading sample template... "
    qiita db load_sample_template $sample_file --study $i
    echo "Ok"

    # Loading raw data
    echo "\tloading raw data... "
    echo -e ">seq\nAAAA" > seqs.fna
    qiita db load_raw --fp seqs.fna --fp_type raw_forward_seqs --filetype FASTQ --study $i
    echo "Ok"

    # Loading prep template
    echo "\tloading prep template... "
    qiita db load_prep_template $prep_file --raw_data $base_id --study $i --data_type "16S"
    echo "Ok"

    # Loading preprocessed data
    echo "\tloading preprocessed data... "
    mkdir -p temp
    echo -e ">seq\nAAAA" > temp/seqs.fna
    qiita db load_preprocessed --study_id $i --params_table preprocessed_sequence_454_params --filedir temp/ --filepathtype preprocessed_fasta --params_id 1 --prep_template_id $base_id
    echo "Ok"

    # Loading processed data
    echo "\tloading processed data... "
    cp $otu_table ${otu_table}_backup
    qiita db load_processed --fp $otu_table --fp_type biom --processed_params_table processed_params_sortmerna --processed_params_id 1 --preprocessed_data_id ${base_id}
    mv ${otu_table}_backup $otu_table
    echo "Ok"

    # # Making study public
    echo "\tmaking study public... "
    echo -e "from qiita_db.study import Study\nStudy(${i}).status = 'public'\n\n" | python
    echo "Ok"
done
