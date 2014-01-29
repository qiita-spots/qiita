from time import localtime

class MetaAnalysisData(object):
    def __init__(self):
        self.user = ''
        self.job = ''
        self.studies = []
        self.datatypes = []
        self.metadata = []
        self.analyses = {}
        self.options = {}

    def __str__(self):
        buildstr = "USER: " + self.user
        buildstr += "\nJOB: " + self.job
        buildstr += "\nSTUDIES: " + str(self.studies)
        buildstr += "\nDATATYPES: " + str(self.datatypes)
        buildstr += "\nMETADATA: " + str(self.metadata)
        buildstr += "\nANALYSES: " + str(self.analyses)
        buildstr += "\nOPTIONS: " + str(self.options)
        return buildstr

    #tornado sends form data in unicode, convert to ascii for ease of use
    def set_user(self, user):
        self.user = user.encode('ascii')

    def set_job(self, job):
        if job == '':
            time = localtime()
            self.job = '-'.join(map(str,[time.tm_year, time.tm_mon, time.tm_mday,
                time.tm_hour, time.tm_min, time.tm_sec]))
        else:
            self.job = job.encode('ascii')

    def set_studies(self, studies):
        self.studies = [study.encode('ascii') for study in studies]

    def set_datatypes(self, datatypes):
        self.datatypes = [datatype.encode('ascii') for datatype in datatypes]

    def set_metadata(self, metadata):
        self.metadata = [m.encode('ascii') for m in metadata]

    def set_analyses(self, datatype, analyses):
        self.analyses[datatype] = [a.encode('ascii') for a in analyses]

    def set_options(self, datatype, analysis, options):
        self.options[datatype + ':' + analysis] = options

    def get_user(self):
        return self.user

    def get_job(self):
        return self.job

    def get_studies(self):
        return self.studies

    def get_datatypes(self):
        return self.datatypes

    def get_metadata(self):
        return self.metadata

    def get_analyses(self, datatype):
        if datatype in self.analyses.keys():
            return self.analyses[datatype]
        else:
            raise ValueError('Datatype not part of analysis!')

    def get_options(self, datatype, analysis):
        if datatype + ':' + analysis in self.options.keys():
            return self.options[datatype + ':' + analysis]
        else:
            raise ValueError('Datatype or analysis passed not part of analysis!')

    def iter_options(self, datatype, analysis):
        if datatype + ':' + analysis in self.options.keys():
            optdict = self.options[datatype + ':' + analysis]
            for opt in optdict:
                yield opt, optdict[opt]
        else:
            raise ValueError('Datatype or analysis passed not part of analysis!')

    def html(self):
        html = '<table width="100%"><tr><td width="34%""><h3>Studies</h3>'
        for study in self.get_studies():
            html += study + "<br />"
        html += '</td><td width="33%"><h3>Metadata</h3>'
        for metadata in self.get_metadata():
            html += metadata + "<br />"
        html += '</td><td width="33%"><h3>Datatypes</h3>'
        for datatype in self.get_datatypes():
            html += datatype + "<br />"
        html += "</td><tr></table>"
        html += '<h3>Option Settings</h3>'
        for datatype in self.get_datatypes():
            for analysis in self.get_analyses(datatype):
                html += ''.join(['<table width=32%" style="display: \
                    inline-block;"><tr><td><b>',datatype,' - ',
                analysis, '</b></td></tr><tr><td>'])
                for opt, value in self.iter_options(datatype, analysis):
                    html += ''.join([opt, ':', str(value), '<br />'])
                html += '</td></tr></table>'
        return html