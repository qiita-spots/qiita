import os
DEBUG = True
DIRNAME = os.path.dirname(__file__)
STATIC_PATH = os.path.join(DIRNAME, 'static')
TEMPLATE_PATH = os.path.join(DIRNAME, 'templates')

import logging
import sys
#log linked to the standard error stream
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)-8s - %(message)s',
                    datefmt='%d/%m/%Y %Hh%Mm%Ss')
console = logging.StreamHandler(sys.stderr)

import base64
import uuid
COOKIE_SECRET = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)

#analyses available in QIIME. Don't forget the options template!
SINGLE = [
#         'TopiaryExplorer_Visualization',
#         'Heatmap',
#         'Taxonomy_Summary',
        'Alpha_Diversity',
        'Beta_Diversity',
        ]
COMBINED = [
        'Procrustes',
#         'Network_Analysis',
        ]