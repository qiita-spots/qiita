_SITEBASE = {
    'logo': "/static/img/logo-clear.png",
    'title': "Qiita",
    'navbar_color': "#2c2c2c",
    'navbar_highlight': "#c0392b",
    'navbar_text_color': "#999999",
    'navbar_text_hover': "white",
}

_INDEX = {
    'text_bg': "#eeeeee",
    'text_color': "black",
    'header': "<i>Qiita</i>: Spot Patterns",
    'text': """<p align="justify">
  Qiita (<i>canonically pronounced cheetah</i>) is an entirely
  <strong>open-source</strong> microbiome storage and analysis resource that
  can run on everything from your laptop to a supercomputer. It is built on top
  of the widely used <a target=_blank href="http://qiime.org">QIIME</a>
  package, and enables the exploration of -omics data.
  </p>
  <br />
  <p align="left">This resource powers the
  <a target=_blank href="http://www.earthmicrobiome.org">
  Earth Microbiome Project</a> and the
  <a target=_blank href="https://ibdmdb.org/">
  Inflammatory Bowel Disease Multi'omics Database</a>.</p>
  <br />
  <p align="left">
    Qiita is built on top of the following open-source technologies:
    <ul>
      <li><a target=_blank href="http://qiime.org">QIIME</a></li>
      <li><a target=_blank href="http://scikit-bio.org">scikit-bio</a></li>
      <li><a target=_blank href="http://emperor.colorado.edu">EMPeror</a></li>
      <li><a target=_blank href="http://biom-format.org">BIOM-Format</a></li>
      <li><a target=_blank href="http://ipython.org">IPython</a></li>
      <li><a target=_blank href="http://numpy.org">NumPy</a></li>
      <li><a target=_blank href="http://scipy.org">SciPy</a></li>
      <li><a target=_blank href="http://tornadoweb.org">Tornado</a></li>
      <li><a target=_blank href="http://redis.io">Redis</a></li>
      <li><a target=_blank href="http://www.postgresql.org">PostgreSQL</a></li>
    </ul>
  </p>"""
}

_STUDY_LIST = {
    'example_search': "env_matter = soil"
}

portal_styling = {
    'sitebase': _SITEBASE,
    'index': _INDEX,
    'study_list': _STUDY_LIST
}
