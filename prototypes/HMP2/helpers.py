from os import walk

def get_available_analyses():
    combined = [analysis.split('.')[0] for analysis in walk('templates/meta_opts/combined').next()[2]]
    single = [analysis.split('.')[0] for analysis in walk('templates/meta_opts/single').next()[2]]
    combined.remove('OTU_Table')
    single.remove('OTU_Table')
    return single, combined