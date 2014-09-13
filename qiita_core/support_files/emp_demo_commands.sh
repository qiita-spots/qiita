####
#### Only collecting the "good" files -- No need to do this
####
# mkdir usable_files
# list="550 632 638 659 662 678 713 722 723 755 776 804 805 807 808 809 846 861 864 894 910 925 933 940 945 958 963 990 1001 1030 1031 1034 1035 1036 1037 1038 1041 1043 1056 1064 1098 1197 1198 1222 1235 1240 1242 1288 1289 1481 1521 1526 1578 1579 1580 1621 1622 1627 1642 1665 1673 1674 1692 1694 1696 1702 1717 1734 1736 1740 1747 1748 1774 1799 1883 2080 2182 2229 2338"
# for i in $list; do cp EMP_STUDIES/study_${i}_split_library_seqs_and_mapping/study_${i}_mapping_file.txt usable_files/; cp EMP_TABLES/closed_ref/study_${i}/otu_table.biom usable_files/otu_table_${i}.biom; done

####
#### Fixing mapping files -- No need to redo this
####
## Step 1: find the missing fields and create a new mapping file with them
# qiita_env drop_env --env demo
# qiita_env make_env --env demo
# qiita_db load_study --owner demo@microbio.me --title 'Cannabis Soil Microbiome' --info study_config_1.txt
# for map_file in `ls usable_files/*file.txt`; do
#    columns=`qiita_db load_sample_template --fp ${map_file} --study 1 2>&1 > /dev/null | grep set | awk -F '[' '{print $2}' | sed "s/[^a-zA-Z0-9,_]//g" | awk -F ',' '{ string=""; for (i=1; i<=NF; i++) { string = string"\t"$i } print string}'`
#    values="";for c in $columns; do if [ "$c" == 'has_physical_specimen' ] || [ "$c" == 'has_extracted_data' ] ; then values=${values}"\ttrue"; elif [ "$c" == 'collection_timestamp' ]; then values=${values}"\t'08/07/2014 10:00:00'"; else values=${values}"\t1" ; fi; done
#    echo -e "#SampleID${columns}\temp_status_id\tdata_type_id" > ${map_file//.txt}_missing_cols.txt
#    for sid in `tail +2 ${map_file} | awk '{print $1}'`; do
#        echo -e "${sid}${values}\t3\t1" >> ${map_file//.txt}_missing_cols.txt
#    done
# done


####
#### Adding studies to qiita
####
## Creating final mapping files, doing it here cause in case of a failure we can start from here
for m in `ls usable_files/*_missing_cols.txt`
do
    merge_mapping_files.py -m ${m},${m//_missing_cols.txt}.txt -o ${m//_missing_cols.txt}_fixed.txt
done

for m in `ls usable_files/*_missing_cols.txt`
do
    merge_mapping_files.py -m ${m},${m//_missing_cols.txt}.txt -o ${m//_missing_cols.txt}_fixed_prep.txt
done

qiita_env drop_env --env demo
qiita_env make_env --env demo

study_id=0

for map_file in `ls usable_files/*_fixed.txt`
do
    echo "++++++++++++++++++++++"
    study_id=$((study_id+1))
    title=`awk -F '\t' -v col=TITLE 'NR==1{for(i=1;i<=NF;i++){if($i==col){c=i;break}} print $c} NR>1{print $c}' ${map_file} | sort | uniq | grep -vw TITLE | head -n 1`
    number_samples_collected=`wc -l ${map_file} | awk '{print $1}'`
    description=`awk -F '\t' -v col=Description 'NR==1{for(i=1;i<=NF;i++){if($i==col){c=i;break}} print $c} NR>1{print $c}' ${map_file} | sort | uniq | grep -vw Description | head -n 1`

    echo $study_id $map_file $title
    
    # inserting study
    echo -e "[required]\ntimeseries_type_id = 1\nmetadata_complete = True\nmixs_compliant = True\nportal_type_id = 3\nprincipal_investigator = Earth Microbiome Project, emp@earthmicrobiome.org, CU Boulder\nreprocess = False\nstudy_alias = $title\nstudy_description = $description\nstudy_abstract = $description\nefo_ids = 1\n[optional]\nnumber_samples_collected = $number_samples_collected\nnumber_samples_promised = $number_samples_collected\n" > study_config.txt
    qiita_db load_study --owner demo@microbio.me --title "$title" --info study_config.txt
    
    # inserting mapping file
    qiita_db load_sample_template --fp $map_file --study $study_id

    # inserting raw data
    echo -e ">seq\nAAAA" > seqs.fna
    qiita_db load_raw_data --fp seqs.fna --fp_type raw_sequences --filetype 454 --study $study_id
    qiita_db load_prep_template --fp ${map_file//.txt}_prep.txt --raw_data $study_id
    mkdir -p temp

    echo -e ">seq\nAAAA" > temp/seqs.fna
    qiita_db load_preprocessed_data --study_id $study_id --params_table preprocessed_sequence_454_params --filedir temp/ --filepathtype preprocessed_sequences --params_id 1 --raw_data_id $study_id
    name=`basename ${map_file//_mapping_file_fixed.txt}`
    qiita_db load_processed_data --fp usable_files/otu_table_${name##study_}.biom --fp_type biom --processed_params_table processed_params_uclust --processed_params_id 1 --preprocessed_data_id ${study_id}
    echo "----------------------"
done

# setting all studies public
echo -e 'from qiita_db.study import Study\nfor i in range(75):\n   Study(i+1).status = "public"\n\n' | python