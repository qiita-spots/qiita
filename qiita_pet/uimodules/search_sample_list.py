from .base_uimodule import BaseUIModule


class SearchSampleList(BaseUIModule):
    def render(self, study_id, meta_headers,
               proc_data_dict, proc_data_samples):

        return self.render_string(
            "search_sample_list.html", meta_headers=meta_headers, sid=study_id,
            proc_data_dict=proc_data_dict, proc_data_samples=proc_data_samples)
