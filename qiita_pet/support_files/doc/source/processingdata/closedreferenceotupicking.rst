Closed-Reference OTU Picking
----------------------------
* **Pick Closed-Reference OTUs**: Removes sequences that do not match those found in a database
  * **Input data** (required): data being close referenced 
  * **Parameter Set** (required): Chooses the database to be compared to
    * **16S OTU Picking**:
      * **Defaults**: Compares to Greengenes 16S Database
       * **Greengenes Citation**: *McDonald, D., Price, M. N., Goodrich, J., Nawrocki, E. P., DeSantis, T. Z., Probst, A., Anderson, G. L., Knight, R.,  Hugenholtz, P. (2012). “An improved Greengenes taxonomy with explicit ranks for ecological and evolutionary analyses of bacteria and archaea.” The ISME Journal. 6(3): 610–618.*
      * **Defaults-parallel**: Compares to GreenGenes 16S database but performs it with multi-threading
       * **Greengenes Citation**:  *McDonald, D., Price, M. N., Goodrich, J., Nawrocki, E. P., DeSantis, T. Z., Probst, A., Anderson, G. L., Knight, R.,  Hugenholtz, P. (2012). “An improved Greengenes taxonomy with explicit ranks for ecological and evolutionary analyses of bacteria and archaea.” The ISME Journal. 6(3): 610–618.*
      * **Silva 119**: Compares to Silva 119 Database
       * **18S OTU picking**
       * **Silve 119 Citation**: *Quast, C., Pruesse, E., Yilmaz, P., Gerken, J., Schweer, T., Yarza, P., Peplies, J., Glöckner, F. O. (2013). “The SILVA ribosomal RNA gene database project: improved data processing and web-based tools”. Nucl. Acids Res. 41 (D1): D590-D596.*
      * **UNITE 7**: Compares to UNITE Database
       * **ITS OTU Picking**
       * **UNITE Citation**: *Abarenkov, K., Nilsson, R. H., Larsson, K., Alexander, I. J., Eberhardt, U., Erland, S., Høiland, K., Kjøller, R., Larsson, E., Pennanen, R., Sen, R., Taylor, A. F. S., Tedersoo, L., Ursing, B. M., Vrålstad, T., Liimatainen, K., Peintner, U., Kõljalg, U. (2010). “The UNITE database for molecular identification of fungi - recent updates and future perspectives”. New Phytologist. 186(2): 281-285.*
  * **Default Parameters** (required)
   * **Reference-seq** (required): Path to blast database (Greengenes, Silva 119, UNITE 7) as a fasta file
   * **Reference-tax** (required): Path to corresponding taxonomy file (Greengenes, Silva 119, UNITE 7)
   * **Similarity** (required): Sequence similarity threshold
   * **Sortmerna coverage** (required): Minimum percent query coverage (of an alignment) to consider a hit, expressed as a fraction between 0 and 1 
   * **Sortmerna e_value** (required): the maximum e-value when clustering (local sequence alignment tool for filtering, mapping, and OTU picking) can expect to see by chance when searching a database
   * **Sortmerna max-pos** (required): The maximum number of positions per seed to store in the indexed database
   * **Threads** (required): number of threads to use per job
   * **SortMeRNA Citation**: *Kopylova, E., Noe, L., Touzet, H. (2012). “SortMeRNA: fast and accurate filtering of ribosomal RNAs in metatranscriptomic data”. Bioinformatics. 28 (24) 3211-7.*
 * **QIIME Citation**: *Nacas-Molina, J.A., Peralta-Sánchez, J.M., González, A., McMurdie, P.J., Vázquez-Baeza, Y., Xu, Z., Ursell, L.K., Lauber, C., Zhou, H., Song S.J., Huntley, J., Ackermann, G.L., Berg-Lyons, D., Holmes, S., Caporaso, J.G., Knight, R. (2013). “Advancing Our Understanding of the Human Microbiome Using QIIME”. Methods in Enzymology. (531): 371-444*
 * **Closed Reference Citation**: *Chou, H.H., Holmes, M.H. (2001). “DNA sequence quality trimming and vector removal”. Bioinformatics. 17 (12):1093–1104.*
